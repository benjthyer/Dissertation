import numpy as np
from diffusion_utils import Simulate_Diffusion

#def Simulate_Diffusion(D0_a2, Ea, T, t, R=8.314):

step_data = np.array([
    [170, 300],
    [180, 463],
    [190, 550],
    [200, 500],
    [210, 475],
    [220, 450],
    [230, 425],
    [225, 908],
    [215, 450],
    [205, 520],
    [195, 1106],
    [185, 740],
    [175, 920],
    [200, 260],
    [210, 520],
    [220, 1167],
    [230, 370],
    [240, 320],
    [245, 250],
    [250, 210],
    [245, 270],
    [240, 320],
    [235, 370],
    [230, 420],
    [225, 652],
    [220, 500],
    [230, 500],
    [235, 450],
    [240, 400],
    [245, 350],
    [250, 300],
    [250, 300],
    [250, 300],
    [250, 10250],
    [100, 7200],
    [240, 785],
    [100, 1589]]
)

Ea_kJ_mol= 157.14018276283093
D0_a2= 10413541.075148752


Fcum = Simulate_Diffusion(D0_a2, Ea=Ea_kJ_mol*1000, T=step_data[:,0], t=step_data[:,1])

for i, step in enumerate(step_data):
    if i > 0:
        prev = Fcum[i-1]
    else:
        prev = 0
    print(f'step {i}, {step[1]} minutes at {step[0]}C: Fcum = {Fcum[i]:.2f} Yield Frac: {Fcum[i]-prev}')
    
    