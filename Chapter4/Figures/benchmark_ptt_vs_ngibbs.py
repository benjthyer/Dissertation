"""
Benchmark: full PetThermoTools (alphaMELTS) equilibration vs. nGibbs.

What is compared, for each batch size N (256 ... 32768):

  * PTT full equilibration -- N / 256 isobaric MELTS cooling paths
    (1155 -> 900 C, dT = 1 C, so 256 equilibria per path).  Each path is a
    sequential MELTS run; the N / 256 paths are distributed across worker
    processes by ptt.isobaric_crystallisation(multi_processing=True), called
    in batches of MAX_WORKERS paths so that every worker runs exactly one
    path.  (A worker process cannot run a second MELTS path: the alphaMELTS
    library keeps process-global state, so the second path fails on its
    first step and PTT drops it silently -- with N / 256 > MAX_WORKERS only
    one path per worker came back.)

  * nGibbsNoProp (CPU and GPU) -- MELTS102Emulator{CPU,GPU}.ForwardMB(
    outputs=['ptt_out']) on the same N (P, T, bulk) rows: phase assemblage,
    modes and compositions only.  GPU timing includes host->device transfer
    and copying the ptt tables back, and is CUDA-synchronised.

  * nGibbs + parallel props (CPU and GPU) -- each of the above plus
    calc_phase_props_MELTS_parallel on its own output table (alphaMELTS
    supCalc phase properties on CPU workers, fixed assemblage, no
    minimisation).  Liquid rows whose composition has a negative SiO2
    component in the MELTS liquid basis are screened out first (untimed; see
    screen_melts_liquid) -- MELTS cannot evaluate them and each one costs an
    OSError plus a library re-initialisation attempt.

GPU lines are skipped (NaN) if CUDA is not available.  PTT is only timed up to
N = PTT_MAX_N (8192); larger N are left NaN, so that line simply stops there.

NOTE: calc_phase_props_MELTS(_parallel) does NOT equilibrate.  It evaluates the
MELTS EOS for the assemblage nGibbs already predicted, which is why it is so
much cheaper than a real PTT path.  The PTT line here is the true
equilibration cost.

Every path uses a different bulk composition: a typical MORB with each oxide
multiplied by N(1, 0.1) noise (seeded, renormalised to 100 wt%).  The same
compositions and P-T conditions are fed to nGibbs.  The composition sets are
nested (N = 512 uses the 256 set plus one more path, etc.).

Results: benchmark_results_ptt_vs_ngibbs.csv and three 300 dpi PDFs in
generated/ next to this script.  Run with --plot-only to re-plot from an
existing CSV, or --max-log2 K to stop at N = 2**K (e.g. 9 for a quick check).

Uses only the installed ``petthermotools`` and ``ngibbs`` packages
(pip install -e <checkout>); nothing is put on sys.path.
"""

from pathlib import Path
import sys
import contextlib
import multiprocessing

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---- Benchmark settings -------------------------------------------------- #
T_START_C   = 1155.0
T_END_C     = 900.0
DT_C        = 1.0
STEPS_PER_PATH = int(round((T_START_C - T_END_C) / DT_C)) + 1   # 256
P_BAR       = 2000.0            # isobaric pressure for every path
NOISE_SIGMA = 0.1               # multiplicative N(1, sigma) per oxide
SEED        = 42
PTT_TIMEOUT = 3600              # s; PTT's default (300 s) can cut off big groups
PTT_MAX_N   = 8192              # PTT is not timed above this (NaN): its parallel speedup
                                # saturates well below it, so larger N only adds hours
MAX_STALLED_PASSES = 1          # abort PTT after this many passes returning no new paths
                                # (its own loop would retry the same failing workers forever)

# 2^8 = 256 ... 2^15 = 32 768  (N = 128 skipped: < one full path)
BATCH_SIZES = [2**k for k in range(8, 16)]

CSV_PATH = OUT_DIR / "benchmark_results_ptt_vs_ngibbs.csv"

MORB = {
    "SiO2":  48.68,
    "TiO2":   1.01,
    "Al2O3": 17.64,
    "Cr2O3":  0.03,
    "FeO":    7.59,
    "Fe2O3":  0.89,
    "MgO":    9.10,
    "CaO":   12.45,
    "Na2O":   2.65,
    "K2O":    0.03,
    "P2O5":   0.08,
    "H2O":    0.20,
}


def perturbed_compositions(n_paths, sigma=NOISE_SIGMA, seed=SEED):
    """n_paths MORB variants: x_i *= N(1, sigma), clipped >= 0, renormalised to 100."""
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(seed)
    base = np.array(list(MORB.values()), dtype=float)
    noise = rng.normal(loc=1.0, scale=sigma, size=(n_paths, base.size))
    comps = np.clip(base * noise, 0.0, None)
    comps *= 100.0 / comps.sum(axis=1, keepdims=True)
    return pd.DataFrame(comps, columns=list(MORB.keys()))


OXIDE_MW = dict(SiO2=60.0843, TiO2=79.8658, Al2O3=101.961, Cr2O3=151.990, FeO=71.844,
                MnO=70.9374, MgO=40.3044, CaO=56.0774, Na2O=61.9789, K2O=94.196, P2O5=141.945)


def screen_melts_liquid(ptt_out, phase="liquid1"):
    """Drop liquid rows MELTS cannot evaluate; returns how many were dropped.

    rhyolite-MELTS 1.0.2 liquid components put Si into Fe2SiO4, MnSi0.5O2, Mg2SiO4
    (after MgCr2O4), CaSiO3 (after Ca3(PO4)2), Na2SiO3 and KAlSiO4, leaving

        n(SiO2 component) = SiO2 - FeO/2 - MnO/2 - (MgO - Cr2O3)/2
                            - (CaO - 3 P2O5) - Na2O - 2 K2O          (moles)

    When this is negative calcPhaseProperties prints "Liquid component SiO2 has
    negative mole fraction" and fails.  Such rows are near-solidus residual liquids
    nGibbs extrapolates poorly (e.g. ~30 wt% Na2O at 900 C); their liquid mass is
    set to 0 so calc_phase_props_MELTS_parallel skips them.
    """
    if phase not in ptt_out:
        return 0
    liq = ptt_out[phase].reset_index(drop=True)
    m = {ox: liq[f"{ox}_Liq"].fillna(0).to_numpy() / mw if f"{ox}_Liq" in liq else 0.0
         for ox, mw in OXIDE_MW.items()}
    n_sio2 = (m["SiO2"] - 0.5 * m["FeO"] - 0.5 * m["MnO"] - 0.5 * (m["MgO"] - m["Cr2O3"])
              - (m["CaO"] - 3 * m["P2O5"]) - m["Na2O"] - 2 * m["K2O"])
    mass = ptt_out["mass_g"][phase]
    bad = (mass.to_numpy() > 0) & (n_sio2 < 0)
    ptt_out["mass_g"].loc[bad, phase] = 0.0
    return int(bad.sum())


def plot_results(df):
    import numpy as np
    import matplotlib.pyplot as plt

    N = df["N"].to_numpy()
    lines = [
        # (label, column, color, linestyle)
        ("PTT full equilibration",                  "t_ptt_s",               "gray",    "-"),
        ("nGibbsNoProp (CPU)",                      "t_ngibbs_cpu_s",        "crimson", "-"),
        ("nGibbs (CPU) + parallel MELTS properties", "t_ngibbs_cpu_props_s", "crimson", "--"),
        ("nGibbsNoProp (GPU)",                      "t_ngibbs_gpu_s",        "royalblue", "-"),
        ("nGibbs (GPU) + parallel MELTS properties", "t_ngibbs_gpu_props_s", "royalblue", "--"),
    ]
    # Drop lines with no data (e.g. GPU columns on a machine without CUDA)
    lines = [l for l in lines if l[1] in df and df[l[1]].notna().any()]

    # 1) Wall time
    plt.figure()
    for label, col, c, ls in lines:
        plt.loglog(N, df[col], label=label, color=c, linestyle=ls, marker="o", ms=3)
    plt.xlabel("Number of Assemblages (N)")
    plt.ylabel("Wall Time (s)")
    plt.grid(True, which="both", alpha=0.4)
    plt.title("MELTS v1.0.2: PTT Equilibration vs. nGibbs — Total Time")
    plt.legend(fontsize=8)
    plt.savefig(OUT_DIR / "ptt_vs_ngibbs_time.pdf", dpi=300, bbox_inches="tight")
    plt.close()

    # 2) Throughput
    plt.figure()
    for label, col, c, ls in lines:
        plt.semilogx(N, N / df[col], label=label, color=c, linestyle=ls, marker="o", ms=3)
    plt.yscale("log")
    plt.xlabel("Number of Assemblages (N)")
    plt.ylabel("Assemblages per second")
    plt.grid(True, which="both", alpha=0.4)
    plt.title("MELTS v1.0.2: PTT Equilibration vs. nGibbs — Throughput")
    plt.legend(fontsize=8)
    plt.savefig(OUT_DIR / "ptt_vs_ngibbs_per_second.pdf", dpi=300, bbox_inches="tight")
    plt.close()

    # 3) Speedup relative to PTT
    plt.figure()
    for label, col, c, ls in lines[1:]:
        plt.loglog(N, df["t_ptt_s"] / df[col], label=f"{label} speedup", color=c, linestyle=ls, marker="o", ms=3)
    plt.axhline(1.0, color="gray", lw=0.8)
    plt.xlabel("Number of Assemblages (N)")
    plt.ylabel("Speedup over PTT equilibration (×)")
    plt.grid(True, which="both", alpha=0.4)
    plt.title("Relative Speedup of nGibbs over PTT")
    plt.legend(fontsize=8)
    plt.savefig(OUT_DIR / "ptt_vs_ngibbs_relative.pdf", dpi=300, bbox_inches="tight")
    plt.close()


# ---- Guard required for multiprocessing on Windows ---------------------- #
if __name__ == "__main__":
    multiprocessing.freeze_support()

    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")

    if "--plot-only" in sys.argv:
        plot_results(pd.read_csv(CSV_PATH))
        sys.exit(0)

    if "--max-log2" in sys.argv:
        _k = int(sys.argv[sys.argv.index("--max-log2") + 1])
        BATCH_SIZES = [n for n in BATCH_SIZES if n <= 2**_k]

    from time import perf_counter
    from tqdm import tqdm

    import petthermotools as ptt
    from petthermotools.MELTS import calc_phase_props_MELTS_parallel
    from petthermotools.core_config import MAX_WORKERS
    import torch
    from ngibbs.engine.models import MELTS102EmulatorCPU, MELTS102EmulatorGPU

    HAVE_GPU = torch.cuda.is_available() and MELTS102EmulatorGPU is not None
    if not HAVE_GPU:
        print("[warn] No CUDA device / GPU emulator -- GPU columns will be NaN.")

    def sync_gpu():
        if HAVE_GPU:
            torch.cuda.synchronize()

    def time_ngibbs(emulator, x, gpu):
        """(seconds, ptt_out) for one ForwardMB call; GPU calls are synchronised."""
        if gpu:
            sync_gpu()
        t0 = perf_counter()
        out = emulator.ForwardMB(x, headers=input_headers, outputs=["ptt_out"])["ptt_out"]
        if gpu:
            sync_gpu()
        return perf_counter() - t0, out

    class PTTStalled(RuntimeError):
        """PTT's retry loop made no progress."""

    class PTTProgress:
        """Stdout filter that rewrites PTT's bare "Completed X %" lines.

        PTT prints that line once per pass of its retry loop (Path.py), i.e.
        after every wave of worker processes, with no context.  A pass that
        returns no new paths prints the same percentage again and PTT simply
        launches another wave -- so a run of identical 0.0 % lines means the
        workers are returning nothing (timeouts or crashes), not progress.
        This reports paths done, elapsed time, a rough ETA and flags stalls.
        All other output passes through untouched.
        """

        def __init__(self, n_paths, stream):
            self.n_paths, self.stream = n_paths, stream
            self.t0 = perf_counter()
            self.n_pass = 0
            self.n_stalled = 0
            self.last_pct = 0.0     # a first pass at 0 % already counts as stalled
            self.buf = ""

        def write(self, s):
            self.buf += s
            while "\n" in self.buf:
                line, self.buf = self.buf.split("\n", 1)
                if line.startswith("Completed "):
                    self._progress(line)
                else:
                    self.stream.write(line + "\n")
            return len(s)

        def flush(self):
            self.stream.flush()

        def _progress(self, line):
            pct = float(line.split()[1])
            self.n_pass += 1
            elapsed = perf_counter() - self.t0
            msg = (f"    PTT pass {self.n_pass}: {round(pct / 100 * self.n_paths)}/{self.n_paths} paths done "
                   f"({pct:.1f} %), {elapsed:.0f} s elapsed")
            if 0 < pct < 100:
                msg += f", ~{elapsed * (100 - pct) / pct:.0f} s remaining"
            stalled = pct == self.last_pct and pct < 100
            if stalled:
                msg += "  [no new paths returned this pass]"
            self.last_pct = pct
            self.stream.write(msg + "\n")
            if stalled:
                self.n_stalled += 1
                if self.n_stalled >= MAX_STALLED_PASSES:
                    # Raised from inside PTT's print(): unwinds its retry loop,
                    # which otherwise relaunches the same failing workers forever.
                    raise PTTStalled(f"PTT made no progress for {self.n_stalled} pass(es) "
                                     f"at {pct:.1f} % -- aborting instead of retrying")

    def time_props(ptt_out):
        """(seconds, liquid rows screened out) for calc_phase_props_MELTS_parallel."""
        n_screened = screen_melts_liquid(ptt_out)   # untimed, see its docstring
        t0 = perf_counter()
        calc_phase_props_MELTS_parallel(ptt_out)
        return perf_counter() - t0, n_screened

    input_headers = ["Pressure(System_main)", "Temperature(System_main)"] + list(MORB.keys())
    T_path = np.linspace(T_START_C, T_END_C, STEPS_PER_PATH)   # same grid PTT builds internally

    all_comps = perturbed_compositions(BATCH_SIZES[-1] // STEPS_PER_PATH)
    all_comps.to_csv(OUT_DIR / "benchmark_ptt_vs_ngibbs_compositions.csv", index=False)

    def ngibbs_input(comps):
        """(n_paths*256, 2+n_ox) array: every path's full T grid at P_BAR, path-major."""
        n_paths = len(comps)
        P = np.full(n_paths * STEPS_PER_PATH, P_BAR)
        T = np.tile(T_path, n_paths)
        C = np.repeat(comps.to_numpy(), STEPS_PER_PATH, axis=0)
        return np.column_stack([P, T, C]).astype(np.float32)

    print(f"Parallel workers: {MAX_WORKERS}")
    print(f"Path: {T_START_C:.0f} -> {T_END_C:.0f} C, dT = {DT_C} C ({STEPS_PER_PATH} steps), P = {P_BAR:.0f} bar\n")

    # Warm-up so the first timed nGibbs calls don't carry one-off init cost
    # (CUDA context / kernel selection on the GPU especially)
    _x_warm = ngibbs_input(all_comps.iloc[:1])
    MELTS102EmulatorCPU.ForwardMB(_x_warm, headers=input_headers, outputs=["ptt_out"])
    if HAVE_GPU:
        MELTS102EmulatorGPU.ForwardMB(_x_warm, headers=input_headers, outputs=["ptt_out"])
        sync_gpu()

    records = []
    for N in tqdm(BATCH_SIZES, desc="batch sizes", unit="batch"):
        n_paths = N // STEPS_PER_PATH
        comps = all_comps.iloc[:n_paths].reset_index(drop=True)
        x = ngibbs_input(comps)
        tqdm.write(f"\n  N={N:>6d} ({n_paths} paths x {STEPS_PER_PATH} steps)")

        # -- nGibbs CPU, then + parallel MELTS properties on its table ----
        t_cpu, out_cpu = time_ngibbs(MELTS102EmulatorCPU, x, gpu=False)
        t_cpu_props, n_scr_cpu = time_props(out_cpu)
        tqdm.write(f"    nGibbsNoProp CPU   {t_cpu:9.3f} s   + props {t_cpu_props:8.3f} s  (total {t_cpu + t_cpu_props:.3f} s)"
                   f"  [{n_scr_cpu} liquid rows screened]")

        # -- nGibbs GPU, then + parallel MELTS properties on its table ----
        if HAVE_GPU:
            t_gpu, out_gpu = time_ngibbs(MELTS102EmulatorGPU, x, gpu=True)
            t_gpu_props, n_scr_gpu = time_props(out_gpu)
            tqdm.write(f"    nGibbsNoProp GPU   {t_gpu:9.3f} s   + props {t_gpu_props:8.3f} s  (total {t_gpu + t_gpu_props:.3f} s)"
                       f"  [{n_scr_gpu} liquid rows screened]")
        else:
            t_gpu = t_gpu_props = float("nan")
            n_scr_gpu = 0

        # -- PTT full equilibration ----------------------------------------
        if N > PTT_MAX_N:
            t_ptt = float("nan")
            runs, n_ptt_ok = [], 0
            tqdm.write(f"    PTT equilibration  skipped (N > {PTT_MAX_N})")
        else:
            n_batches = -(-n_paths // MAX_WORKERS)
            tqdm.write(f"    PTT equilibration  starting: {n_paths} paths on {MAX_WORKERS} workers "
                       f"({n_batches} batch(es) of <= {MAX_WORKERS}, one path per worker) ...")
            runs = []
            t0 = perf_counter()
            try:
                # One path per worker process (see module docstring): PTT only ever
                # gives a worker more than one path when paths outnumber cores.
                for b0 in range(0, n_paths, MAX_WORKERS):
                    batch = comps.iloc[b0:b0 + MAX_WORKERS].reset_index(drop=True)
                    with contextlib.redirect_stdout(PTTProgress(len(batch), sys.stdout)):
                        ptt_res = ptt.isobaric_crystallisation(
                            Model="MELTSv1.0.2", bulk=batch,
                            T_start_C=T_START_C, T_end_C=T_END_C, dt_C=DT_C, P_bar=P_BAR,
                            find_liquidus=False, Frac_solid=False, Frac_fluid=False,
                            timeout=PTT_TIMEOUT, multi_processing=True,
                        )
                    # A single-path result is one dict; multi-path is {"Run i": dict}
                    runs += [ptt_res] if "Conditions" in ptt_res else [v for v in ptt_res.values() if isinstance(v, dict) and "Conditions" in v]
            except PTTStalled as err:
                for proc in multiprocessing.active_children():
                    proc.terminate()
                tqdm.write(f"    PTT equilibration  FAILED: {err} (keeping the {len(runs)} paths already returned)")
            t_ptt_raw = perf_counter() - t0
            n_ptt_ok = int(sum(len(r["Conditions"]) for r in runs))

            # PTT can return fewer equilibria than requested (failed paths are dropped
            # silently while still counting as "complete"), so the raw wall time covers
            # only n_ptt_ok equilibria.  Rescale to N, assuming failed rows cost the same.
            t_ptt = t_ptt_raw * N / n_ptt_ok if n_ptt_ok else float("nan")
            tqdm.write(f"    PTT equilibration  {t_ptt_raw:9.3f} s raw  ({len(runs)}/{n_paths} paths, {n_ptt_ok}/{N} equilibria returned)"
                       + (f"  -> {t_ptt:.3f} s scaled to N" if n_ptt_ok and n_ptt_ok != N else ""))
        tqdm.write(f"    speedup vs PTT: CPU {t_ptt / t_cpu:.0f}x / {t_ptt / (t_cpu + t_cpu_props):.1f}x w/ props, "
                   f"GPU {t_ptt / t_gpu:.0f}x / {t_ptt / (t_gpu + t_gpu_props):.1f}x w/ props")

        records.append(dict(
            N=N, n_paths=n_paths,
            t_ngibbs_cpu_s=t_cpu,
            t_props_on_cpu_out_s=t_cpu_props,
            t_ngibbs_cpu_props_s=t_cpu + t_cpu_props,
            t_ngibbs_gpu_s=t_gpu,
            t_props_on_gpu_out_s=t_gpu_props,
            t_ngibbs_gpu_props_s=t_gpu + t_gpu_props,
            t_ptt_s=t_ptt,
            t_ptt_raw_s=t_ptt_raw if N <= PTT_MAX_N else float("nan"),
            ptt_paths_returned=len(runs),
            ptt_equilibria_returned=n_ptt_ok,
            liquid_rows_screened_cpu=n_scr_cpu,
            liquid_rows_screened_gpu=n_scr_gpu,
        ))
        pd.DataFrame(records).to_csv(CSV_PATH, index=False)   # save as we go

    # ---- Summary table --------------------------------------------------- #
    header = (f"{'N':>7}  {'paths':>5}  {'CPU (s)':>9}  {'CPU+props':>10}  {'GPU (s)':>9}  {'GPU+props':>10}  "
              f"{'PTT (s)':>9}  {'PTT eq ok':>9}  {'PTT/CPU':>8}  {'PTT/GPU':>8}")
    print("\n" + header)
    print("-" * len(header))
    for r in records:
        print(f"{r['N']:>7d}  {r['n_paths']:>5d}  {r['t_ngibbs_cpu_s']:>9.4f}  {r['t_ngibbs_cpu_props_s']:>10.4f}  "
              f"{r['t_ngibbs_gpu_s']:>9.4f}  {r['t_ngibbs_gpu_props_s']:>10.4f}  "
              f"{r['t_ptt_s']:>9.2f}  {r['ptt_equilibria_returned']:>9d}  "
              f"{r['t_ptt_s'] / r['t_ngibbs_cpu_s']:>7.0f}x  {r['t_ptt_s'] / r['t_ngibbs_gpu_s']:>7.0f}x")
    print(f"\nResults saved to {CSV_PATH}")

    plot_results(pd.DataFrame(records))
