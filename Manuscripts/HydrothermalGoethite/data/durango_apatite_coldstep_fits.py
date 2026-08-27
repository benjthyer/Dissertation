"""
First-order permeation inversions of the last two steps of each 3-step,
~24 C isothermal ("cold step", CB: 15.0_25.0) permeation sequence recorded
during the encapsulated Durango apatite diffusion run. Most cold-step
sequences in this run only have 2 steps; the handful that have 3 (the first
few analyses) start with a step that is still cooling from the preceding hot
step, so only the last two (near-isothermal, ~24 C) steps of those 3-step
sequences are used here.

With only two data points constraining the two fit parameters (lambda, n0),
each fit is exactly determined (0 degrees of freedom) -- this is a sanity
check on how poorly constrained that leaves lambda and n0, not a definitive
result.

Reads: Encapsulated_Apatite.xlsx, 'Raw Data and Corrections' tab
  - column W  : blank-corrected He yield per step (nCC)
  - column X  : 2-sigma uncertainty on column W
  - column AA : total step time (s)

Outputs:
  durango_coldstep_fits.csv          - lambda, n0 (+/- 1 sigma) per sequence
  durango_coldstep_lambda_vs_n0.png  - fit lambda vs fit n0, with x/y error
                                        bars and the Swets et al. (1961)
                                        expected lambda as a horizontal line
"""
import os
import numpy as np
import pandas as pd
import scipy.optimize
import matplotlib.pyplot as plt

OUTDIR = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(OUTDIR, 'Encapsulated_Apatite.xlsx')
SHEET = 'Raw Data and Corrections'
SWETS_1961_LAMBDA = 1.45e-6  # s^-1, expected 24 C value from Swets et al., 1961

HE_COL = 'BC nCC.1'          # column W: blank-corrected He yield (nCC)
HE_ERR_COL = '2σ.3'     # column X: 2-sigma uncertainty on HE_COL
TIME_COL = 'total time (seconds)'  # column AA


def forward_permeate(t, lamb, n0):
    """Yield due to permeation given rate constant and time. t in seconds, lamb in s^-1"""
    return n0 * (1 - np.exp(-lamb * t))


def forward_permeate1(t, lamb, n0):
    """Step yield between [start, end] times. t is [start, end], each an array."""
    return (n0 * (1 - np.exp(-lamb * t[1]))) - (n0 * (1 - np.exp(-lamb * t[0])))


def accumulate(v):
    out = [v[0]]
    for x in v[1:]:
        out.append(x + out[-1])
    return np.array(out)


def FirstOrdInv(t, He, sigma):
    """Exponential fit for a cold-permeation step sequence; returns (lambda, n0, covmat)."""
    lamb0 = SWETS_1961_LAMBDA
    cumt = [0] + accumulate(t).tolist()
    tinput = np.array([[cumt[i], cumt[i + 1]] for i in range(len(cumt) - 1)]).T
    out, covmat = scipy.optimize.curve_fit(
        forward_permeate1, tinput, He, sigma=sigma, absolute_sigma=True,
        p0=[lamb0, He[0] / (1 - np.exp(-lamb0 * t[0]))], maxfev=20000)
    return out, covmat


# ---------------------------------------------------------------------------
# Load data and find the 3-step cold (CB: 15.0_25.0) sequences
# ---------------------------------------------------------------------------

df = pd.read_excel(XLSX, sheet_name=SHEET, header=2)
df = df[df['Name'].notna() & (df['Name'] != 'total')].reset_index(drop=True)

is_cb = df['Name'] == 'CB: 15.0_25.0'
cb_idx = df.index[is_cb].tolist()

runs = []
cur = [cb_idx[0]]
for a, b in zip(cb_idx[:-1], cb_idx[1:]):
    if b == a + 1:
        cur.append(b)
    else:
        runs.append(cur)
        cur = [b]
runs.append(cur)

three_step_runs = [r for r in runs if len(r) == 3]
print(f"Found {len(three_step_runs)} 3-step cold sequences out of {len(runs)} total cold sequences")

results = []
for run in three_step_runs:
    last_two = run[1:]
    He = df.loc[last_two, HE_COL].to_numpy(dtype=float)
    He_sigma = df.loc[last_two, HE_ERR_COL].to_numpy(dtype=float) / 2  # 2-sigma -> 1-sigma
    t = df.loc[last_two, TIME_COL].to_numpy(dtype=float)

    try:
        (lamb, n0), covmat = FirstOrdInv(t, He, sigma=He_sigma)
        lamb_err, n0_err = np.sqrt(np.diag(covmat))
        print(f"rows {last_two}: lambda = {lamb:.3e} +/- {lamb_err:.3e}, "
              f"n0 = {n0:.3e} +/- {n0_err:.3e}")
    except RuntimeError as e:
        lamb = n0 = lamb_err = n0_err = np.nan
        print(f"rows {last_two}: fit did not converge ({e})")

    results.append({
        'rows': last_two,
        'He': He, 'He_sigma': He_sigma, 't': t,
        'lambda': lamb, 'lambda_sigma': lamb_err,
        'n0': n0, 'n0_sigma': n0_err,
    })

results_df = pd.DataFrame([{
    'rows': r['rows'], 'lambda': r['lambda'], 'lambda_sigma': r['lambda_sigma'],
    'n0': r['n0'], 'n0_sigma': r['n0_sigma'],
} for r in results])
results_df.to_csv(os.path.join(OUTDIR, 'durango_coldstep_fits.csv'), index=False)

# ---------------------------------------------------------------------------
# Plot: fit lambda vs fit n0
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(7, 5.5))
ax.errorbar(results_df['n0'], results_df['lambda'],
            xerr=results_df['n0_sigma'], yerr=results_df['lambda_sigma'],
            fmt='o', capsize=3, color='tab:blue', ecolor='tab:blue',
            label='2-point fits (last two of each 3-step sequence)')
ax.axhline(SWETS_1961_LAMBDA, color='k', linestyle='--',
           label=f'Swets et al., 1961 (λ = {SWETS_1961_LAMBDA:.2e} s$^{{-1}}$)')
# The 2-point fits are exactly-determined (0 dof), so several of them carry
# enormous uncertainties -- symlog keeps both the well- and poorly-constrained
# points readable on the same axes.
ax.set_xscale('symlog', linthresh=1)
ax.set_yscale('symlog', linthresh=1e-7)
ax.set_xlabel('fit n0 (nCC)')
ax.set_ylabel(r'fit $\lambda$ (s$^{-1}$)')
ax.set_title('Durango apatite: 3-step cold sequences\n(last two steps only)')
ax.legend(fontsize=8, loc='best')
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'durango_coldstep_lambda_vs_n0.png'), dpi=200)
plt.show()
