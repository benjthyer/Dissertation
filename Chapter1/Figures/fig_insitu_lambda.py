"""
fig_insitu_lambda.py -- Checks A and B of the Copernicus methods paper.

Check A (MC empty ampoule): in-situ fits of the permeation rate constant
lambda to consecutive isothermal permeation steps, for 3He and 4He.
    generated/InSituLambdaArrhenius.pdf   (a) ln(lambda/T) vs 1e4/T,
                                          (b) lambda(3He)/lambda(4He)
Check B (encapsulated Durango apatite): R^2 of the corrected Arrhenius
array below the high-temperature curl as a function of lambda at 24 C.
    generated/DurangoLambdaSelfCalibration.pdf

Also writes (consumed by the manuscript and SI):
    ../Writing/paper_derived_values.tex       numeric macros quoted in text
    ../Writing/paper_insitu_lambda_table.tex  SI table of the in-situ fits
    generated/data/insitu_lambda_fits.csv
    generated/data/durango_lambda_scan.csv

Geometry + literature predictions (Swets et al. 1961; Jones 1953; Table 1
dimensions) are overlaid ONLY as checks; nothing here uses them as input
except the published Durango correction that Check B rescales.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style
import insitu_lambda as L

apply_style()
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'generated')
OUTD = os.path.join(OUT, 'data')
WRITING = os.path.join(HERE, '..', 'Writing')
os.makedirs(OUTD, exist_ok=True)

# ---------------------------------------------------------------- Check A
fits = L.check_A()
fits['lam_over_pred'] = fits['lam'] / fits['lam_pred']
fits['n0_over_true'] = fits['n0_fit'] / fits['n0_true']
fits.to_csv(os.path.join(OUTD, 'insitu_lambda_fits.csv'), index=False)

f4 = fits[fits.isotope == '4He'].set_index('T_C')
f3 = fits[fits.isotope == '3He'].set_index('T_C')
ratio = f3['lam'] / f4['lam']
ratio_1s = ratio * np.sqrt((f3['lam_1s'] / f3['lam']) ** 2 + (f4['lam_1s'] / f4['lam']) ** 2)
Ea4, _, _ = L.arrhenius_lam_over_T(f4['T_K'], f4['lam'])
Ea3, _, _ = L.arrhenius_lam_over_T(f3['T_K'], f3['lam'])
good = f4.index[f4['N'] >= 3]          # over-determined fits (>= 3 steps)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.4, 9.6), sharex=True)
Tline = np.linspace(100, 300, 200) + 273.15
x = 1e4 / Tline
ISO = {'4He': r'$^4$He', '3He': r'$^3$He'}
for iso, f, mk, col, ls in (('4He', f4, 'o', 'tab:blue', '-'),
                            ('3He', f3, 's', 'tab:orange', '--')):
    ax1.plot(x, np.log(L.lambda_predicted(Tline, L.G_MC_EMPTY, iso) / Tline),
             color=col, ls=ls, lw=1.5,
             label=f'{ISO[iso]}, predicted from geometry + literature')
    y = np.log(f['lam'] / f['T_K'])
    yerr = 2 * f['lam_1s'] / f['lam']
    over = (f['N'] >= 3).to_numpy()
    xx = (1e4 / f['T_K']).to_numpy(); y = y.to_numpy(); yerr = yerr.to_numpy()
    ax1.errorbar(xx[over], y[over], yerr=yerr[over], fmt=mk,
                 color=col, mec='k', capsize=4, label=f'{ISO[iso]}, fit in situ ($\\geq$3 steps)')
    ax1.errorbar(xx[~over], y[~over], yerr=yerr[~over], fmt=mk, mfc='white',
                 color=col, capsize=4, label=f'{ISO[iso]}, fit in situ (2 steps)')
ax1.set_ylabel(r'$\ln(\lambda/T)$  ($\lambda$ in s$^{-1}$, $T$ in K)')
ax1.legend(fontsize=9, loc='lower left')
ax1.grid(True)
ax1.text(0.97, 0.95, '(a)', transform=ax1.transAxes, ha='right', va='top', fontsize=14)

TT = 1e4 / f4['T_K']
over = (f4['N'] >= 3).to_numpy()
ax2.errorbar(TT[over], ratio[over], yerr=2 * ratio_1s[over], fmt='D', color='tab:green',
             mec='k', capsize=4, label=r'This work, $\lambda(^3$He$)/\lambda(^4$He$)$ ($\geq$3 steps)')
ax2.errorbar(TT[~over], ratio[~over], yerr=2 * ratio_1s[~over], fmt='D', mfc='white',
             color='tab:green', capsize=4, label='This work (2 steps)')
ax2.plot(x, L.jones(Tline), color='red', label='Jones (1953)')
ax2.axhline(1, color='k', ls=':', lw=1)
ax2.set_ylim(0.5, 1.6)
ax2.set_ylabel(r'$\lambda(^3$He$)\,/\,\lambda(^4$He$)$')
ax2.set_xlabel(r'$10^4/T$ (K$^{-1}$)')
#ax2.text(0.03, 0.06, 'McMurtry et al. (2019): up to ~1000 (off scale)',
#         transform=ax2.transAxes, fontsize=10, style='italic')
ax2.legend(fontsize=9, loc='upper right')
ax2.grid(True)
ax2.text(0.03, 0.95, '(b)', transform=ax2.transAxes, ha='left', va='top', fontsize=14)
ax2.set_xlim(1e4 / (300 + 273.15), 1e4 / (100 + 273.15))
top = ax1.twiny()
Ct = np.array([100, 150, 200, 250, 300])
top.set_xlim(ax1.get_xlim()); top.set_xticks(1e4 / (Ct + 273.15)); top.set_xticklabels(Ct)
top.set_xlabel('Temperature (°C)')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'InSituLambdaArrhenius.pdf'), dpi=300)
plt.close(fig)

# ---------------------------------------------------------------- Check B
lam_pred24 = L.lambda_predicted(L.T_PERM_DURANGO_K, L.G_DURANGO)
grid = lam_pred24 * np.linspace(0.6, 1.6, 501)
scan, idx = L.check_B(grid, lam_pred24)
scan.to_csv(os.path.join(OUTD, 'durango_lambda_scan.csv'), index=False)
best = scan.loc[scan['R2'].idxmax()]
r2_at_pred = float(np.interp(lam_pred24, scan['lam24'], scan['R2']))

d = L.load_durango()
peaks = []
for drop in idx:                       # leave-one-step-out jackknife
    use = [i for i in idx if i != drop]
    bestj = (-np.inf, np.nan)
    for lam in grid:
        e = L.durango_correct(d, lam_pred24 / lam)
        D = e.loc[use, 'Da2'].to_numpy(float)
        if np.any(~(D > 0)):
            continue
        r2, _ = L.r2_linear(1 / (e.loc[use, 'T_C'].to_numpy() + 273.15), np.log(D))
        if r2 > bestj[0]:
            bestj = (r2, lam)
    peaks.append(bestj[1])
peaks = np.array(peaks)
n = len(peaks)
jk_1s = np.sqrt((n - 1) / n * np.sum((peaks - peaks.mean()) ** 2))

fig, ax = plt.subplots()
ax.plot(scan['lam24'] * 1e6, scan['R2'], color='k', lw=2)
#ax.axvspan((best.lam24 - 2 * jk_1s) * 1e6, (best.lam24 + 2 * jk_1s) * 1e6,
#           color='tab:blue', alpha=0.2, label=r'Data: maximum $R^2$ $\pm 2\sigma$ (jackknife)')
ax.axvline(best.lam24 * 1e6, color='tab:blue', lw=1.5)
ax.axvline(lam_pred24 * 1e6, color='tab:red', ls='--', lw=1.5,
           label=r'Predicted $\lambda_{24}$ from geometry + Swets et al. (1961)')
ax.set_xlabel(r'Trial $\lambda_{24}$ ($10^{-6}$ s$^{-1}$)')
ax.set_ylabel(r'$R^2$ of $\ln(D/a^2)$ vs. $1/T$ ($\leq$300 °C)')
ax.set_ylim(max(0.95, scan['R2'].min()), 1.0)
ax.legend(loc='lower right')
ax.grid(True)
plt.title('Linearity of Durango Apatite Step Heats for Varying $\lambda$_{24}')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'DurangoLambdaSelfCalibration.pdf'), dpi=300)
plt.close(fig)

# ------------------------------------------------- macros + SI table output
fits_all = L.check_A(drop_first=False)
r2_all, r2_adopt, Ea_all = {}, {}, {}
for iso in ('4He', '3He'):
    for F, store in ((fits_all, r2_all), (fits, r2_adopt)):
        g = F[F.isotope == iso]
        store[iso] = L.r2_linear(1 / g['T_K'].to_numpy(), np.log(g['lam'] / g['T_K']).to_numpy())[0]
    g = fits_all[fits_all.isotope == iso]
    Ea_all[iso] = L.arrhenius_lam_over_T(g['T_K'], g['lam'])[0]


def fmt(v, p=2):
    return f'{v:.{p}f}'


steps_T = L.durango_correct(d, 1.0).loc[idx, 'T_C'].to_numpy()
macros = {
    'PaperLamTwentyFourData': fmt(best.lam24 * 1e6),
    'PaperLamTwentyFourDataTwoSigma': fmt(2 * jk_1s * 1e6),
    'PaperLamTwentyFourPred': fmt(lam_pred24 * 1e6),
    'PaperLamTwentyFourRatio': fmt(best.lam24 / lam_pred24),
    'PaperDurangoNsteps': str(len(idx)),
    'PaperDurangoRtwoMax': f'{best.R2:.4f}',
    'PaperDurangoRtwoPred': f'{r2_at_pred:.4f}',
    'PaperEaFourHe': fmt(Ea4, 1),
    'PaperEaThreeHe': fmt(Ea3, 1),
    'PaperEaLit': fmt(4900 * 4.184 / 1e3, 1),
    'PaperLamPredMinPct': fmt(100 * abs(f4.loc[good, 'lam_over_pred'] - 1).min(), 0),
    'PaperLamPredMaxPct': fmt(100 * abs(pd.concat([f4.loc[good, 'lam_over_pred'],
                                                    f3.loc[good, 'lam_over_pred']]) - 1).max(), 0),
    'PaperNzeroMaxPctFourHe': fmt(100 * abs(f4.loc[good, 'n0_over_true'] - 1).max(), 1),
    'PaperNzeroMaxPctThreeHe': fmt(100 * abs(f3.loc[good, 'n0_over_true'] - 1).max(), 1),
    'PaperFirstStepLamRatioMax': fmt(100 * (L.FIRST_STEP_LAM_RATIO_MAX - 1), 0),
    'PaperLamTCumMin': fmt(fits.loc[fits.N >= 3, 'lamt_cum'].min(), 1),
    'PaperLamTCumMax': fmt(fits.loc[fits.N >= 3, 'lamt_cum'].max(), 1),
    'PaperArrRtwoAllFourHe': f'{r2_all["4He"]:.2f}',
    'PaperArrRtwoAllThreeHe': f'{r2_all["3He"]:.2f}',
    'PaperArrRtwoFourHe': f'{r2_adopt["4He"]:.2f}',
    'PaperArrRtwoThreeHe': f'{r2_adopt["3He"]:.2f}',
    'PaperEaAllFourHe': fmt(Ea_all['4He'], 0),
    'PaperRatioMin': fmt(ratio[good].min()),
    'PaperRatioMax': fmt(ratio[good].max()),
    'PaperHoursLamTHalfTwentyFive': fmt(0.5 / L.lambda_predicted(298.15, L.G_MC_EMPTY) / 3600, 0),
    'PaperHoursLamTHalfEighty': fmt(0.5 / L.lambda_predicted(353.15, L.G_MC_EMPTY) / 3600, 0),
}
with open(os.path.join(WRITING, 'paper_derived_values.tex'), 'w', encoding='utf-8') as fh:
    fh.write('% AUTO-GENERATED by Chapter1/Figures/fig_insitu_lambda.py -- do not edit.\n')
    for k, v in macros.items():
        fh.write(f'\\providecommand{{\\{k}}}{{{v}}}\n')

lines = [
    '% AUTO-GENERATED by Chapter1/Figures/fig_insitu_lambda.py -- do not edit.',
    '\\begin{table*}[t]',
    '\\caption{In-situ permeation rate constants of the empty ampoule, fit to consecutive '
    'isothermal permeation steps with Eq.~(\\ref{eq:incyield}) (written in mass-balance form). '
    'The first steps of the 125 and 200\\,\\textdegree C runs are excluded (see main text and '
    'Fig.~\\ref{fig:s-insitu-fits}), leaving exactly determined two-step fits. The last two 250\\,\\textdegree C accumulations (steps 28--29), which '
    'permeate anomalously fast in both isotopes just before the anomalous final measurement, are '
    'also excluded. $n_0$ (true) is known independently from the experiment\'s total yield and is '
    'not used in the fits. $\\lambda_{\\mathrm{pred}}$ is predicted from the measured ampoule '
    'geometry and literature permeabilities \\citep{swets1961,jones1953} and is shown only as a '
    'check. Uncertainties are 1$\\sigma$ from the fit covariance.}',
    '\\label{tab:s-insitu-lambda}',
    '\\centering',
    '\\begin{tabular}{lrrrrrrr}',
    '\\tophline',
    'Isotope & $T$ (\\textdegree C) & Steps & $\\lambda$ ($10^{-5}$\\,s$^{-1}$) & '
    '$\\lambda/\\lambda_{\\mathrm{pred}}$ & $n_0$ fit / true & $\\lambda t_{\\mathrm{cum}}$ & '
    '$\\lambda(^3\\mathrm{He})/\\lambda(^4\\mathrm{He})$ \\\\',
    '\\middlehline',
]
for _, r in fits.sort_values(['T_C', 'isotope'], ascending=[True, False]).iterrows():
    rat = ''
    if r.isotope == '3He':
        rat = f'{ratio[r.T_C]:.3f} $\\pm$ {ratio_1s[r.T_C]:.3f}'
    lines.append(
        f'{ {"4He": "$^4$He", "3He": "$^3$He"}[r.isotope]} & '
        f'{r.T_C:.0f} & {int(r.N)} ({int(r.first_step)}--{int(r.last_step)}) & '
        f'{r.lam * 1e5:.3f} $\\pm$ {r.lam_1s * 1e5:.3f} & {r.lam_over_pred:.3f} & '
        f'{r.n0_over_true:.3f} & {r.lamt_cum:.2f} & {rat} \\\\')
lines += ['\\bottomhline', '\\end{tabular}', '\\end{table*}']
with open(os.path.join(WRITING, 'paper_insitu_lambda_table.tex'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(lines) + '\n')

test = L.first_step_test()
tl = [
    '% AUTO-GENERATED by Chapter1/Figures/fig_insitu_lambda.py -- do not edit.',
    '\\begin{table*}[t]',
    '\\caption{First-step test for the in-situ rate-constant fits of the empty ampoule. Each run of '
    'consecutive isothermal permeation steps is fit with all of its steps and again without its first '
    'step. A first step taken before the glass reached diffusive steady state can only under-permeate, '
    'so removing it raises $\\lambda$ and lowers the inferred starting inventory. The first step is '
    f'rejected if removing it raises $\\lambda$ by more than {100 * (L.FIRST_STEP_LAM_RATIO_MAX - 1):.0f}\\,\\% '
    'in both isotopes; a run left with fewer than three steps is not used, because a two-step fit is '
    'exactly determined. $n_{\\mathrm{start}}$ is the inventory at the start of the run (for the fit '
    'without the first step, its $n_0$ plus the measured first-step yield). $\\chi^2$/dof is undefined '
    'for two-step fits. Uncertainties are 1$\\sigma$.}',
    '\\label{tab:s-first-step-test}',
    '\\centering',
    '\\begin{tabular}{lrrrrrrrl}',
    '\\tophline',
    'Isotope & $T$ (\\textdegree C) & Steps (all / without first) & $\\chi^2$/dof, all & '
    '$\\chi^2$/dof, without first & $\\lambda_{\\mathrm{without}}/\\lambda_{\\mathrm{all}}$ & '
    '$n_{\\mathrm{start,without}}/n_{\\mathrm{start,all}}$ & Run used \\\\',
    '\\middlehline',
]
for _, r in test.sort_values(['T_C', 'isotope'], ascending=[True, False]).iterrows():
    c2 = '--' if np.isnan(r.chi2dof_drop) else f'{r.chi2dof_drop:.1f}'
    tl.append(f'{ {"4He": "$^4$He", "3He": "$^3$He"}[r.isotope]} & {r.T_C:.0f} & '
              f'{int(r.N_all)} / {int(r.N_drop)} & {r.chi2dof_all:.1f} & {c2} & '
              f'{r.lam_ratio:.3f} $\\pm$ {r.lam_ratio_1s:.3f} & {r.n0_ratio:.3f} & '
              f'{"yes" if r.run_used else "no"} \\\\')
tl += ['\\bottomhline', '\\end{tabular}', '\\end{table*}']
with open(os.path.join(WRITING, 'paper_first_step_test_table.tex'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(tl) + '\n')
test.to_csv(os.path.join(OUTD, 'insitu_first_step_test.csv'), index=False)

print(fits[['isotope', 'T_C', 'N', 'lam', 'lam_1s', 'lam_over_pred', 'n0_over_true',
            'lamt_cum']].to_string())
print(macros)
