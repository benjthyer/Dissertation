import numpy as np
import torch
import matplotlib.pyplot as plt
from time import time
from ngibbs.utils.math_utils import mix_compositions, IDX_2D_Lithosphere
from ngibbs.engine.models import HeFESToMarsEmulatorCPU, HeFESToMarsEmulatorGPU

np.random.seed(0)  # fixed seed so the random profiles (and the figure) are reproducible

# Each profile is a conductive lid over an adiabatic (isentropic) mantle, as in a
# 1D seismic-inversion forward model. All profiles are evaluated in one batch on
# the GPU when one is available (HeFESToMarsEmulatorGPU is None otherwise).
if torch.cuda.is_available() and HeFESToMarsEmulatorGPU is not None:
    device = "cuda"
    HeFESToMarsEmulator = HeFESToMarsEmulatorGPU
else:
    device = "cpu"
    HeFESToMarsEmulator = HeFESToMarsEmulatorCPU
print(f"Using the {device.upper()} emulator")

n_pressures = 100  # pressure nodes per profile
n_profiles = 375   # profiles evaluated in parallel (37,500 assemblages in total)

# 2D (profile x pressure) arrays, filled in below by the isentropic and the
# isothermal (conductive) calculations
properties = {prop: np.zeros((n_profiles, n_pressures), dtype=np.float32)
              for prop in ['temperature', 'S', 'rho', 'Vp', 'Vs', 'Kh']}

P_max = 25   # GPa; the Mars emulators are trained to 25.5 GPa
T_min = 220  # K; surface temperature of the conductive lid (fixed in the Mars training data)
pressures = np.linspace(0, P_max, n_pressures)

# Randomly drawn profile parameters:
#   P_lit  -- pressure at the base of the conductive lid, 1.5--9 GPa (stored as an index into `pressures`)
#   S_lit  -- specific entropy (J/g/K) of the underlying isentrope
#   X_mars -- mixing fraction between bulk silicate Earth (0) and bulk silicate Mars (1)
P_lit_idx = np.random.choice(np.where((pressures <= 9) & (pressures >= 1.5))[0], size=n_profiles, replace=True)
P_lit = pressures[P_lit_idx]
S_lit = np.random.choice(np.linspace(1.75, 2.8, n_profiles), size=n_profiles, replace=False)
X_mars = np.random.choice(np.linspace(0, 1, n_profiles), size=n_profiles, replace=False)

# (row, column) index pairs that split every profile at its own P_lit: nodes at
# and below P_lit belong to the isentrope, nodes above it to the conductive lid.
isentropic_IDX, isothermal_IDX = IDX_2D_Lithosphere(P_lit_idx, n_pressures)

# End-member bulk compositions in oxide wt% (Fe3+/Fe_total ~0.1 for Mars, ~0.03 for Earth)
BSMarsOxides = {  # Yoshizaki and McDonough (2020)
    'SiO2': 45.5, 'Al2O3': 3.59, 'FeO': 13.0, 'Fe2O3': 2.1,
    'MgO': 31.0, 'CaO': 2.88, 'Na2O': 0.59, 'Cr2O3': 0.88,
}
BSEarthOxides = {  # McDonough and Sun (1995)
    'SiO2': 45.0, 'Al2O3': 4.45, 'FeO': 7.75, 'Fe2O3': 0.35,
    'MgO': 37.8, 'CaO': 3.55, 'Na2O': 0.36, 'Cr2O3': 0.38,
}

# Column headers tell the emulator what each input column is. The isentropic
# model takes (P, S, composition); the isothermal model takes (P, T, composition).
S_headers = ['P(GPa)(System_main)', 'S(J/g/K)(System_main)']
T_headers = ['P(GPa)(System_main)', 'T(K)(System_main)']

# One mixed bulk composition per profile. mix_compositions returns a dict whose
# key order may differ from the inputs, so the headers are taken from its output.
comp_array = np.zeros((n_profiles, len(BSEarthOxides)), dtype=np.float32)
for i, fraction in enumerate(X_mars):
    compositions = mix_compositions([BSEarthOxides, BSMarsOxides], [1 - fraction, fraction])
    if i == 0:
        S_headers += list(compositions.keys())
        T_headers += list(compositions.keys())
    comp_array[i] = list(compositions.values())

# --- Step 1: the adiabatic segment (isentropic emulator) ---------------------
# One input row per (profile, pressure) node below the lid: [P, S, composition]
isentropic_input_array = np.zeros((isentropic_IDX[0].shape[0], comp_array.shape[1] + 2))
isentropic_input_array[:, 2:] = comp_array[isentropic_IDX[0]]
isentropic_input_array[:, 1] = S_lit[isentropic_IDX[0]]
isentropic_input_array[:, 0] = pressures[isentropic_IDX[1]]

# ForwardMB predicts the stable assemblage (as mass-balanced component moles)
# and, for the isentropic model, the temperature at each (P, S).
t0 = time()
with torch.no_grad():
    output = HeFESToMarsEmulator.ForwardMB(
        isentropic_input_array, headers=S_headers, outputs=['component_moles', 'temperature']
    )
print(f'Isentropic emulator: {isentropic_input_array.shape[0]} assemblages in {time() - t0:.2f} s')

T_em = np.asarray(output['temperature'].detach().cpu(), dtype=np.float64).reshape(-1)
properties['temperature'][isentropic_IDX] = T_em

# (N, 2) array of [P (GPa), T (K)] at which to evaluate the bulk properties
PT = np.stack([isentropic_input_array[:, 0], T_em], axis=1)

# Temperature is already known, so only the other properties are requested
property_names = [prop for prop in properties if prop != 'temperature']

# Bulk properties from the vectorized HeFESTo equations of state, evaluated on
# the emulated assemblages at the emulated temperatures
t1 = time()
eos_isentropic = HeFESToMarsEmulator._compute_bulk_EOS_properties(
    output['component_moles'].to(device),
    torch.tensor(PT, dtype=torch.float64, device=device),
    property_names=property_names,
)
print(f'Bulk properties:     {isentropic_input_array.shape[0]} assemblages in {time() - t1:.2f} s')

for property_name, computed in eos_isentropic.items():
    properties[property_name][isentropic_IDX] = computed

# --- Step 2: the conductive lid (isothermal emulator) ------------------------
# Temperature rises linearly from T_min at the surface to T_lit, the isentrope
# temperature at P_lit. linspace runs to P_lit and drops its last point, so
# the node at P_lit keeps its isentropic value and is not computed twice.
T_conduct = np.empty(0,)
T_lit = []
for i, idx in enumerate(P_lit_idx):
    newT_lit = properties['temperature'][i, idx]
    T_lit.append(newT_lit)
    T_conduct = np.append(T_conduct, np.linspace(T_min, newT_lit, idx + 1)[:-1])

properties['temperature'][isothermal_IDX] = T_conduct

# One input row per node in the lid: [P, T, composition]
isothermal_input_array = np.zeros((isothermal_IDX[0].shape[0], comp_array.shape[1] + 2))
isothermal_input_array[:, 2:] = comp_array[isothermal_IDX[0]]
isothermal_input_array[:, 1] = T_conduct
isothermal_input_array[:, 0] = pressures[isothermal_IDX[1]]

t0 = time()
with torch.no_grad():
    iso_output = HeFESToMarsEmulator.ForwardMB(
        isothermal_input_array, headers=T_headers, outputs=['component_moles']
    )
print(f'Isothermal emulator: {isothermal_input_array.shape[0]} assemblages in {time() - t0:.2f} s')

# Same equation-of-state step; here the [P, T] columns are the inputs themselves
t1 = time()
eos_isothermal = HeFESToMarsEmulator._compute_bulk_EOS_properties(
    iso_output['component_moles'].to(device),
    torch.tensor(isothermal_input_array[:, :2], dtype=torch.float64, device=device),
    property_names=property_names,
)
print(f'Bulk properties:     {isothermal_input_array.shape[0]} assemblages in {time() - t1:.2f} s')

for property_name, computed in eos_isothermal.items():
    properties[property_name][isothermal_IDX] = computed

# --- Plot four randomly chosen profiles --------------------------------------
chosen_plot_rows = np.random.choice(np.arange(n_profiles), size=4, replace=False)

fig, axes = plt.subplots(1, 5, figsize=(16, 7), sharey=True)

prop_configs = [  # (data, x-axis label, panel title)
    (properties['temperature'][chosen_plot_rows], 'Temperature (K)', 'Temperature'),
    (properties['rho'][chosen_plot_rows],         'Density (g/cm$^3$)', 'Density'),
    (properties['Vp'][chosen_plot_rows],          'Vp (km/s)',       'P-wave Velocity'),
    (properties['Vs'][chosen_plot_rows],          'Vs (km/s)',       'S-wave Velocity'),
    (properties['Kh'][chosen_plot_rows],          'Ks (GPa)',        'Isentropic Bulk Modulus'),
]

for ax, (data, xlabel, title) in zip(axes, prop_configs):
    for i, idx in enumerate(chosen_plot_rows):
        ax.plot(data[i], pressures,
                label=f'P_lit={P_lit[idx]:.1f} GPa, T_lit={T_lit[idx]:.0f} K, X_Mars={X_mars[idx]:.2f}')
        if title == 'Temperature':  # mark the base of the conductive lid
            ax.scatter(T_lit[idx], P_lit[idx], color='k', marker='x', s=100)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

axes[0].set_ylabel('Pressure (GPa)')
axes[0].invert_yaxis()
fig.legend(*axes[0].get_legend_handles_labels(), loc='lower center', ncol=2)
fig.suptitle(f'Conductive lithosphere over an adiabatic asthenosphere: 4 of {n_profiles} BSMars-BSEarth mixtures', fontsize=13)
plt.tight_layout(rect=(0, 0.08, 1, 1))  # leave room for the legend below the panels
plt.show()
