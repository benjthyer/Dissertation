"""
Benchmark: PetThermoTools (alphaMELTS) isobaric cooling paths vs. the nGibbs MELTS emulator.

Two independent parts, each writing its own CSV to generated/:

  ptt     benchmark_results_ptt_scaling.csv
          PTT full equilibration on isobaric MELTS 1.0.2 cooling paths
          (1200 -> 1000 C, dT = 1 C, so 201 equilibria per path, P = 2 kbar),
          w * p paths for w in WORKERS and p in PATHS_PER_WORKER, run as p
          consecutive ptt.multi_path(cores=w) calls of w paths each (one
          path per worker process per call), timed together.  A worker
          process cannot solve a second MELTS path: in PTT's path_multi the
          second path fails on its first step, already counts as done, and is
          silently dropped (a single multi_path call with p paths per worker
          returns only ceil(p / 2) of them).  The p-sweep at fixed w gives the
          per-path cost on w workers (slope) and start-up cost (intercept);
          plot_benchmark_combined.py extrapolates that line.

  ngibbs  benchmark_results_ngibbs_melts.csv
          MELTS102EmulatorCPU.ForwardMB(outputs=['ptt_out']) on N rows of the
          same kind of cooling path (N = 16 ... 262144, the batch sizes of the
          HeFESTo emulator benchmark; one path holds 201 rows), then
          PetThermoTools' calc_phase_props_MELTS_parallel on its
          output table (alphaMELTS supCalc phase properties on PTT's default
          worker count, fixed assemblage, no minimisation).  Liquid rows whose
          composition has a negative SiO2 component in the MELTS liquid basis
          are screened out first (untimed; see screen_melts_liquid).  Each N
          is repeated NGIBBS_REPEATS times (a fresh emulator call, then
          properties on its own table) and the median of each time is kept.

Every path uses a different bulk composition: a typical MORB with each oxide
multiplied by N(1, 0.1) noise (seeded, renormalised to 100 wt%).  The sets are
nested, so a run with more paths reuses the compositions of every smaller run.

Failed equilibria are not counted: the ptt CSV keeps the raw wall time and the
number of equilibria PTT actually returned, and the plot uses the latter as N.

Usage
    python benchmark_ptt_vs_ngibbs.py                 # both parts
    python benchmark_ptt_vs_ngibbs.py --part ptt      # or --part ngibbs
    python benchmark_ptt_vs_ngibbs.py --out-dir DIR   # write CSVs elsewhere (e.g. a test run)

Uses only the installed ``petthermotools`` and ``ngibbs`` packages
(pip install -e <checkout>); nothing is put on sys.path.
"""

from pathlib import Path
import sys
import contextlib
import multiprocessing

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR / "generated"

# ---- Benchmark settings -------------------------------------------------- #
T_START_C   = 1200.0
T_END_C     = 1000.0
DT_C        = 1.0
STEPS_PER_PATH = int(round((T_START_C - T_END_C) / DT_C)) + 1   # 201
P_BAR       = 2000.0            # isobaric pressure for every path
NOISE_SIGMA = 0.1               # multiplicative N(1, sigma) per oxide
SEED        = 42
PTT_TIMEOUT = 600               # s per path; multi_path allows up to 3x this per wave

WORKERS          = (1, 4, 8)
PATHS_PER_WORKER = (1, 2, 3, 4, 5)
MAX_STALLED_PASSES = 1          # abort PTT after this many passes returning no new paths
                                # (its own loop would retry the same failing workers forever)

# 2^4 = 16 ... 2^18 = 262 144 rows for the emulator, as in the HeFESTo emulator benchmark
NGIBBS_SIZES = [2**k for k in range(4, 19)]
NGIBBS_REPEATS = 3              # median of this many timings per N

PTT_CSV    = "benchmark_results_ptt_scaling.csv"
NGIBBS_CSV = "benchmark_results_ngibbs_melts.csv"

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


# ---- Guard required for multiprocessing on Windows ---------------------- #
if __name__ == "__main__":
    multiprocessing.freeze_support()

    import numpy as np
    import pandas as pd
    from time import perf_counter

    part = sys.argv[sys.argv.index("--part") + 1] if "--part" in sys.argv else "all"
    if part not in ("all", "ptt", "ngibbs"):
        sys.exit(f"--part must be ptt, ngibbs or all, not {part!r}")
    if "--out-dir" in sys.argv:
        OUT_DIR = Path(sys.argv[sys.argv.index("--out-dir") + 1]).resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    import petthermotools as ptt

    class PTTStalled(RuntimeError):
        """PTT's retry loop made no progress."""

    class PTTProgress:
        """Stdout filter that rewrites PTT's bare "Completed X %" lines.

        PTT prints that line once per pass of its retry loop (Path.py), i.e.
        after every wave of worker processes, with no context.  A pass that
        returns no new paths prints the same percentage again and PTT simply
        launches another wave -- so a run of identical lines means the
        workers are returning nothing (timeouts or crashes), not progress.
        This reports paths done and elapsed time and aborts on a stall.
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
            stalled = pct == self.last_pct and pct < 100
            self.last_pct = pct
            self.stream.write(f"      pass {self.n_pass}: {round(pct / 100 * self.n_paths)}/{self.n_paths} paths "
                              f"({pct:.1f} %), {perf_counter() - self.t0:.0f} s"
                              + ("  [no new paths returned]" if stalled else "") + "\n")
            if stalled:
                self.n_stalled += 1
                if self.n_stalled >= MAX_STALLED_PASSES:
                    # Raised from inside PTT's print(): unwinds its retry loop,
                    # which otherwise relaunches the same failing workers forever.
                    raise PTTStalled(f"no progress for {self.n_stalled} pass(es) at {pct:.1f} %")

    def path_rows(comps, n_rows):
        """First n_rows of the path-major (P, T, bulk) table for these paths."""
        T_path = T_START_C - DT_C * np.arange(STEPS_PER_PATH)   # same grid PTT builds internally
        T = np.tile(T_path, len(comps))
        C = np.repeat(comps.to_numpy(), STEPS_PER_PATH, axis=0)
        P = np.full(len(T), P_BAR)
        return np.column_stack([P, T, C])[:n_rows].astype(np.float32)

    max_paths = max(max(WORKERS) * max(PATHS_PER_WORKER), -(-NGIBBS_SIZES[-1] // STEPS_PER_PATH))
    all_comps = perturbed_compositions(max_paths)
    all_comps.to_csv(OUT_DIR / "benchmark_ptt_vs_ngibbs_compositions.csv", index=False)
    print(f"Path: {T_START_C:.0f} -> {T_END_C:.0f} C, dT = {DT_C} C ({STEPS_PER_PATH} steps), P = {P_BAR:.0f} bar\n")

    # ---- PTT: workers x paths-per-worker grid ------------------------------ #
    if part in ("all", "ptt"):
        records = []
        for w in WORKERS:
            for p in PATHS_PER_WORKER:
                n_paths = w * p
                print(f"  PTT  {w} worker(s) x {p} path(s) = {n_paths} paths ({n_paths * STEPS_PER_PATH} equilibria)")
                runs = []
                t0 = perf_counter()
                try:
                    # One path per worker per call (see module docstring)
                    for b0 in range(0, n_paths, w):
                        bulk = all_comps.iloc[b0:b0 + w].reset_index(drop=True)
                        with contextlib.redirect_stdout(PTTProgress(w, sys.stdout)):
                            res = ptt.multi_path(
                                cores=w, Model="MELTSv1.0.2", bulk=bulk,
                                T_start_C=T_START_C, T_end_C=T_END_C, dt_C=DT_C, P_bar=P_BAR,
                                find_liquidus=False, Frac_solid=False, Frac_fluid=False,
                                timeout=PTT_TIMEOUT, multi_processing=True,
                            )
                        # A single-path result is one dict; multi-path is {"Run i": dict}
                        runs += [res] if "Conditions" in res else [v for v in res.values() if isinstance(v, dict) and "Conditions" in v]
                except PTTStalled as err:
                    for proc in multiprocessing.active_children():
                        proc.terminate()
                    print(f"      FAILED: {err}")
                t = perf_counter() - t0
                n_ok = int(sum(r["Conditions"]["T_C"].notna().sum() if "T_C" in r["Conditions"]
                               else len(r["Conditions"]) for r in runs))
                print(f"      {t:8.2f} s  ({len(runs)}/{n_paths} paths, {n_ok}/{n_paths * STEPS_PER_PATH} equilibria)"
                      f"  -> {n_ok / t:.1f} equilibria/s")
                records.append(dict(workers=w, paths_per_worker=p, n_paths=n_paths,
                                    N_requested=n_paths * STEPS_PER_PATH, paths_returned=len(runs),
                                    equilibria_returned=n_ok, t_s=t))
                pd.DataFrame(records).to_csv(OUT_DIR / PTT_CSV, index=False)   # save as we go
        print(f"\n  -> {OUT_DIR / PTT_CSV}\n")

    # ---- nGibbs MELTS emulator (CPU) + PTT phase properties ---------------- #
    if part in ("all", "ngibbs"):
        from petthermotools.MELTS import calc_phase_props_MELTS_parallel
        from petthermotools.core_config import MAX_WORKERS
        from ngibbs.engine.models import MELTS102EmulatorCPU

        headers = ["Pressure(System_main)", "Temperature(System_main)"] + list(MORB.keys())
        # Warm-up so the first timed call doesn't carry one-off init cost
        MELTS102EmulatorCPU.ForwardMB(path_rows(all_comps.iloc[:1], STEPS_PER_PATH), headers=headers, outputs=["ptt_out"])

        records = []
        for N in NGIBBS_SIZES:
            x = path_rows(all_comps, N)
            t_emu, t_props = [], []
            for _ in range(NGIBBS_REPEATS):
                # calc_phase_props_MELTS_parallel adds to its table, so every repeat
                # evaluates properties on the output of its own emulator call
                t0 = perf_counter()
                out = MELTS102EmulatorCPU.ForwardMB(x, headers=headers, outputs=["ptt_out"])["ptt_out"]
                t_emu.append(perf_counter() - t0)
                n_scr = screen_melts_liquid(out)   # untimed, see its docstring
                t0 = perf_counter()
                calc_phase_props_MELTS_parallel(out)
                t_props.append(perf_counter() - t0)
            t_emu, t_props = float(np.median(t_emu)), float(np.median(t_props))
            print(f"  nGibbs N={N:>6d}  emulator {t_emu:8.3f} s  + PTT props {t_props:8.3f} s"
                  f"  (median of {NGIBBS_REPEATS})  [{n_scr} liquid rows screened]")
            records.append(dict(N=N, t_ngibbs_cpu_s=t_emu, t_props_s=t_props,
                                t_ngibbs_cpu_props_s=t_emu + t_props, n_repeats=NGIBBS_REPEATS,
                                props_workers=MAX_WORKERS, liquid_rows_screened=n_scr))
            pd.DataFrame(records).to_csv(OUT_DIR / NGIBBS_CSV, index=False)
        print(f"\n  -> {OUT_DIR / NGIBBS_CSV}")
