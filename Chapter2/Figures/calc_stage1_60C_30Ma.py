"""
Partial He loss and apparent He age for the Winsor goethite Stage 1
reference domain held isothermally at 60°C for 30 Ma.

  1. Fractional He loss with no ingrowth (all He present at t = 0),
     via Forward_Diffuse (Fechtig & Kalbitzer 1966).
  2. Apparent He age t' with concomitant production and diffusive loss,
     via wolfEQ (Wolf et al. 1998).

D0/a^2 and Ea are the central (M) Stage 1 regression, read from
Figures/generated/data/stage1_regression_cache.json (run
prepare_regression_cache.py first if it's missing).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_utils import Forward_Diffuse, wolfEQ
from thermochr_utils import load_stage1_cache

T_C = 60
t_yr = 30E6
sec_per_yr = 365.25 * 24 * 3600

stage1 = load_stage1_cache()
D0_a2 = stage1['M']['D0_a2']        # s^-1
Ea = stage1['M']['Ea_cal_mol']      # cal/mol
D_a2 = D0_a2 * np.exp(-Ea / (1.987 * (T_C + 273.15)))

F_lost = Forward_Diffuse(D_a2 * t_yr * sec_per_yr)
t_app = wolfEQ(t=t_yr, D_a2=D_a2)

print(f'Stage 1 reference domain (M): D0/a^2 = {D0_a2:.4e} s^-1, Ea = {Ea:.0f} cal/mol')
print(f'D/a^2 at {T_C}°C = {D_a2:.4e} s^-1')
print(f'Dt/a^2 after {t_yr / 1E6:.0f} Ma = {D_a2 * t_yr * sec_per_yr:.4e}')
print(f'No-ingrowth fractional He loss: {F_lost:.4f}  (retained: {1 - F_lost:.4f})')
print(f"Apparent He age t' (Wolf eq.): {t_app / 1E6:.3f} Ma  (t'/t = {t_app / t_yr:.4f})")
