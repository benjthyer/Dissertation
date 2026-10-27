import numpy as np
import torch
from time import time
from ngibbs.utils.math_utils import mix_compositions, IDX_2D_Split_3Part
from ngibbs.engine.models import HeFESToEmulatorCPU, HeFESToEmulatorGPU

# Each profile is a whole-mantle column: a conductive lid over an
# adiabatic (isentropic) mantle over a conductive thermal boundary layer
# (TBL) at the core-mantle boundary (CMB). All profiles are evaluated in
# one batch, on the GPU when one is available.
HeFESToEmulator = HeFESToEmulatorGPU or HeFESToEmulatorCPU
device = HeFESToEmulator.device
print(f"Using the {str(device).upper()} emulator")

n_pressures = 175  # pressure nodes per profile
n_profiles = 201   # profiles evaluated in parallel
P_CMB = 135        # GPa
T_surface = 300    # K
pressures = np.linspace(0, P_CMB, n_pressures)

# Profile parameters, swept together from the first profile to the last
X_basalt = np.linspace(1, 0, n_profiles)     # basalt fraction
S_ad = np.linspace(2.3, 2.8, n_profiles)     # isentrope entropy (J/g/K)
P_lid = np.linspace(8, 1, n_profiles)        # base of the lid (GPa)
P_TBL = np.linspace(132, 125, n_profiles)    # top of the TBL (GPa)
T_CMB = np.linspace(3500, 5000, n_profiles)  # CMB temperature (K)

# Snap both transitions to the nearest pressure node. The isentrope
# covers nodes lid_idx to TBL_idx; the lid lies above it, the TBL below.
lid_idx = np.abs(pressures - P_lid[:, None]).argmin(axis=1)
TBL_idx = np.abs(pressures - P_TBL[:, None]).argmin(axis=1)
P_lid, P_TBL = pressures[lid_idx], pressures[TBL_idx]

# (row, column) index pairs into the (profile x pressure) grid for each
# regime. The lid and the TBL are both conductive, so they are evaluated
# together.
TBL_IDX, isentropic_IDX, lid_IDX = IDX_2D_Split_3Part(
    lid_idx, TBL_idx + 1, n_pressures)
conductive_IDX = tuple(np.concatenate(pair)
                       for pair in zip(lid_IDX, TBL_IDX))

# End-member bulk compositions in HeFESTo element moles, from the
# SILICAadiabat and BASALTadiabat standards ('O' sets the ferric iron)
SILICA = {'Si': 4.35196, 'Mg': 4.35196, 'Fe': 0.51993, 'Ca': 0.29376,
          'Al': 0.40504, 'Na': 0.05391, 'Cr': 0.02345, 'O': 14.54576}
BASALT = {'Si': 4.61116, 'Mg': 1.33197, 'Fe': 0.61701, 'Ca': 1.22855,
          'Al': 1.81090, 'Na': 0.39533, 'Cr': 0.00508, 'O': 15.35841}
mixes = [mix_compositions([SILICA, BASALT], [1 - x, x])
         for x in X_basalt]
comp_headers = list(mixes[0])
comp_array = np.array([list(mix.values()) for mix in mixes])

# Results on the (profile x pressure) grid, filled one regime at a time
properties = {prop: np.zeros((n_profiles, n_pressures))
              for prop in ['temperature', 'S', 'rho', 'Vp', 'Vs', 'Kh']}
indexer = HeFESToEmulator.isentropic_emulator.ml_indexer
mass_phasedict = indexer.mass_phasedict  # phase name -> column
phase_fractions = np.zeros((n_profiles, n_pressures,
                            len(mass_phasedict)))

def emulate(IDX, condition, condition_header, outputs):
    """Emulate the stable assemblage at each node in IDX from its
    pressure, its S or T, and its composition."""
    inputs = np.column_stack(
        [pressures[IDX[1]], condition, comp_array[IDX[0]]])
    headers = ['P(GPa)(System_main)', condition_header] + comp_headers
    with torch.no_grad():
        return HeFESToEmulator.ForwardMB(inputs, headers=headers,
                                         outputs=outputs)

def store(IDX, output, T):
    """Fill the grid at IDX with the phase mass fractions, and with bulk
    properties from the vectorized HeFESTo equations of state evaluated
    on the emulated assemblages."""
    properties['temperature'][IDX] = T
    mass_percent = output['phase_tables'][1].cpu().numpy()
    phase_fractions[IDX] = mass_percent / 100
    PT = torch.tensor(np.column_stack([pressures[IDX[1]], T]),
                      dtype=torch.float64, device=device)
    eos = HeFESToEmulator._compute_bulk_EOS_properties(
        output['component_moles'].to(device), PT,
        property_names=['S', 'rho', 'Vp', 'Vs', 'Kh'])
    for name, values in eos.items():
        properties[name][IDX] = values

# --- Step 1: the adiabatic mantle (isentropic emulator) --------------
# Run first, because both conductive layers start from the isentrope
# temperatures, which the isentropic model predicts at each (P, S).
t0 = time()
output = emulate(isentropic_IDX, S_ad[isentropic_IDX[0]],
                 'S(J/g/K)(System_main)',
                 ['component_moles', 'phase_tables', 'temperature'])
T_isentrope = output['temperature'].cpu().numpy().reshape(-1)
store(isentropic_IDX, output, T_isentrope)
print(f'Adiabatic mantle:  {len(isentropic_IDX[0])} assemblages '
      f'in {time() - t0:.2f} s')

# --- Step 2: the lid and the TBL (isothermal emulator) ---------------
# Temperature is linear in pressure: in the lid from T_surface to the
# isentrope at P_lid, and in the TBL from the isentrope at P_TBL to
# T_CMB. Each linspace drops the node it shares with the isentrope.
T = properties['temperature']
T_lid = [np.linspace(T_surface, T[i, j], j + 1)[:-1]
         for i, j in enumerate(lid_idx)]
T_TBL = [np.linspace(T[i, j], T_CMB[i], n_pressures - j)[1:]
         for i, j in enumerate(TBL_idx)]
T_conductive = np.concatenate(T_lid + T_TBL)

t0 = time()
output = emulate(conductive_IDX, T_conductive, 'T(K)(System_main)',
                 ['component_moles', 'phase_tables'])
store(conductive_IDX, output, T_conductive)
print(f'Conductive layers: {len(conductive_IDX[0])} assemblages '
      f'in {time() - t0:.2f} s')
