"""Burial chi^2 grid for N = 4 at t_form 180, 195, 210 Ma, parallel over grid rows."""
import os, sys, json
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winsor_he43_model as M
import winsor_he43_mdd_free as F
DATA = os.path.join(M.DATA_OUTDIR, 'mdd_free', 'absolute')
res = json.load(open(os.path.join(DATA, 'N4.json')))
SM = F.SpectrumModelFree(M.load_spectrum(), res['f'], res['r'])
def nodes(tf, Tm, tp):
    return [tf, tp, 50.0, 0.0], [M.T_SURF, Tm, M.T_SURF, M.T_SURF]
def ev(a):
    tf, tp = a
    out = []
    for Tm in np.arange(30.0, 90.01, 1.0):
        c, age, _ = SM.evaluate(*nodes(tf, Tm, tp))
        out.append((tf, tp, Tm, c, age))
    return out
if __name__ == '__main__':
    items = [(tf, tp) for tf in (180.0, 195.0, 210.0) for tp in np.arange(55.0, tf - 2.5 + 1e-9, 2.5)]
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 2) as p:
        rows = [r for chunk in p.map(ev, items) for r in chunk]
    pd.DataFrame(rows, columns=['t_form_Ma', 't_peak_Ma', 'T_max_C', 'chi2', 'bulk_age_Ma']).to_csv(
        os.path.join(DATA, 'maps_N4.csv'), index=False)
    print('done', len(rows))
