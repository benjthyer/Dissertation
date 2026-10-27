import multiprocessing
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from time import time

# Mauna Loa estimated primary melt composition from Wieser et al. 2025
ML_starting = {
    'SiO2_Liq': 48.5858,
    'TiO2_Liq': 1.4381,
    'Al2O3_Liq': 9.73,
    'FeOt_Liq': 10.144,
    'MgO_Liq': 20.0,
    'CaO_Liq': 7.2186,
    'Na2O_Liq': 1.7327,
    'K2O_Liq': 0.3227,
    'H2O_Liq': 0.2,
    'Fe3Fet_Liq': 0.12
}

# Guard required for multiprocessing on Windows: each PTT worker re-imports this
# file, and without it would rerun phaseDiagram_calc (and reload nGibbs) itself.
if __name__ == "__main__":
    multiprocessing.freeze_support()
    import petthermotools as ptt

    ptt.nGibbs_bridge._ensure_ngibbs_loaded()

    start_time = time()
    PD_ML = ptt.phaseDiagram_calc(Model = "MELTSv1.0.2",
                                    bulk = ML_starting,
                                    T_C = np.linspace(1100,1400,20),
                                    P_bar = np.linspace(250,5000,20),
                                    refine = 2,
                                    i_max = 3)
    print(f"rhyolite-MELTS Phase diagram calculation time: {time() - start_time:.2f} seconds")

    start_time = time()
    nPD_ML = ptt.phaseDiagram_calc(Model = "nMELTSv1.0.2NoProp", # No properties needed for this analysis
                                    bulk = ML_starting,
                                    T_C = np.linspace(1100,1400,20),
                                    P_bar = np.linspace(250,5000,20))

    print(f"nGibbs Phase diagram calculation time: {time() - start_time:.2f} seconds")

    ptt.plot_phaseDiagram_multi({'nGibbs': nPD_ML, 'rhyolite-MELTS v1.0.2': PD_ML})