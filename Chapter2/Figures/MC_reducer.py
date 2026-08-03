"""
Reduces MC noble-gas mass-spectrometer sensitivities from the November
2023 bracketing standards, then applies them to a batch of isothermal
step-heat analyses.

Builds on thermochr_utils.MCHeReducer, adding back the diagnostic
sensitivity-vs-time plots that class doesn't produce on its own (this
script is the only consumer of them).

Reads:
  STD_nov.csv                             - bracketing standard analyses
  111923SmallSIlicaTubeISOTHERMALS.csv    - isothermal step analyses (headerless MC export)

Outputs:
  SensitivitiesHeMC.pdf        - standard sensitivity curves vs. time
  interpSensitivitiesHeMC.pdf  - sensitivities interpolated at analysis times
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thermochr_utils import MCHeReducer

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DATA_DIR)
OUTDIR = os.path.join(DATA_DIR, 'generated')
os.makedirs(OUTDIR, exist_ok=True)


class PlottingMCHeReducer(MCHeReducer):
    """MCHeReducer with the diagnostic sensitivity plots this script needs."""

    def plot(self):
        fig, ax1 = plt.subplots()
        color = 'tab:red'
        ax1.set_xlabel(f'time (days) after {self.t0}')
        ax1.set_ylabel('4He Sensitivity nCCSTP/fA', color=color)
        ax1.plot(self.x / (3600 * 24), self.model4, color=color)
        ax1.plot(self.x / (3600 * 24), self.model4 + 2 * self.model4sigma, alpha=0.4, linestyle='--', color=color)
        ax1.plot(self.x / (3600 * 24), self.model4 - 2 * self.model4sigma, alpha=0.4, linestyle='--', color=color)
        ax1.errorbar(self.Dt / (3600 * 24), self.sens4, yerr=2 * np.array(self.sigma4), linestyle='', color=color)
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()
        color = 'tab:blue'
        ax2.set_ylabel('3He Sensitivity pCCSTP/cps', color=color)
        ax2.plot(self.x / (3600 * 24), self.model3, color=color)
        ax2.plot(self.x / (3600 * 24), self.model3 + 2 * self.model3sigma, alpha=0.4, linestyle='--', color=color)
        ax2.plot(self.x / (3600 * 24), self.model3 - 2 * self.model3sigma, alpha=0.4, linestyle='--', color=color)
        ax2.errorbar(self.Dt / (3600 * 24), self.sens3, yerr=2 * np.array(self.sigma3), linestyle='', color=color)
        ax2.tick_params(axis='y', labelcolor=color)

        plt.title('Helium Sensitivities MC')
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR, 'SensitivitiesHeMC.pdf'), dpi=300)
        plt.close(fig)

    def reduce(self, DIFFCELL, form='%m/%d/%Y  %I:%M %p', plot=False, sens_out=False, uncertainties=False):
        out = super().reduce(DIFFCELL, form=form, sens_out=sens_out, uncertainties=uncertainties)
        if plot:
            self._plot_interp()
        return out

    def _plot_interp(self):
        fig, ax1 = plt.subplots()
        std_reltimes = (self.Dt > (min(self.AnalDT) - 3600 * 24)) & (self.Dt < (max(self.AnalDT) + 3600 * 24))
        model_reltimes = (self.x > (min(self.AnalDT) - 3600 * 24)) & (self.x < (max(self.AnalDT) + 3600 * 24))

        color = 'tab:red'
        ax1.set_xlabel(f'time (days) after {self.t0}')
        ax1.set_ylabel('4He Sensitivity nCCSTP/fA', color=color)
        ax1.plot(self.x[model_reltimes] / (3600 * 24), self.model4[model_reltimes], color=color)
        ax1.scatter(self.Dt[std_reltimes] / (3600 * 24), self.sens4[std_reltimes], color=color,
                    label='Measured 4He Sensitivity')
        ax1.errorbar(self.Dt[std_reltimes] / (3600 * 24), self.sens4[std_reltimes],
                     yerr=2 * np.array(self.sigma4)[std_reltimes], color=color, alpha=0.5, linestyle='')
        ax1.plot(self.x[model_reltimes] / (3600 * 24),
                 self.model4[model_reltimes] + 2 * self.model4sigma[model_reltimes],
                 alpha=0.4, linestyle='--', color=color)
        ax1.plot(self.x[model_reltimes] / (3600 * 24),
                 self.model4[model_reltimes] - 2 * self.model4sigma[model_reltimes],
                 alpha=0.4, linestyle='--', color=color)
        ax1.scatter(self.AnalDT / (3600 * 24), self.model4[self.sensIND], s=20, marker='x', color='k',
                    label='Interpolated In-run 4He Sensitivity')
        ax1.errorbar(self.AnalDT / (3600 * 24), self.model4[self.sensIND],
                     yerr=2 * np.array(self.model4sigma[self.sensIND]), color='grey', alpha=0.4, linestyle='')
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.legend(loc='upper right', fontsize='small')

        ax2 = ax1.twinx()
        color = 'tab:blue'
        ax2.set_ylabel('3He Sensitivity pCCSTP/cps', color=color)
        ax2.plot(self.x[model_reltimes] / (3600 * 24), self.model3[model_reltimes], color=color)
        ax2.scatter(self.Dt[std_reltimes] / (3600 * 24), self.sens3[std_reltimes], color=color,
                    label='Measured 3He Sensitivity')
        ax2.errorbar(self.Dt[std_reltimes] / (3600 * 24), self.sens3[std_reltimes],
                     yerr=2 * np.array(self.sigma3)[std_reltimes], color=color, alpha=0.5, linestyle='')
        ax2.plot(self.x[model_reltimes] / (3600 * 24),
                 self.model3[model_reltimes] + 2 * self.model3sigma[model_reltimes],
                 alpha=0.4, linestyle='--', color=color)
        ax2.plot(self.x[model_reltimes] / (3600 * 24),
                 self.model3[model_reltimes] - 2 * self.model3sigma[model_reltimes],
                 alpha=0.4, linestyle='--', color=color)
        ax2.scatter(self.AnalDT / (3600 * 24), self.model3[self.sensIND], s=25, marker='+', color='k',
                    label='Interpolated In-run 3He Sensitivity')
        ax2.errorbar(self.AnalDT / (3600 * 24), self.model3[self.sensIND],
                     yerr=2 * np.array(self.model3sigma[self.sensIND]), color='grey', alpha=0.4, linestyle='')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.legend(loc='lower right', fontsize='small')

        plt.title('Helium Sensitivities MC')
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR, 'interpSensitivitiesHeMC.pdf'), dpi=300)
        plt.close(fig)


reducer = PlottingMCHeReducer('STD_nov.csv')
reducer.plot()

analyses = pd.read_csv('111923SmallSIlicaTubeISOTHERMALS.csv', header=None).to_numpy()
reducer.reduce(analyses, form='%m/%d/%Y  %H:%M:%S', plot=True)
