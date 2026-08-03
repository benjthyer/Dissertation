
#FIG 1!!!
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
import pandas as pd
import scipy
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import apply_style, LEGEND_SIZE
apply_style()

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUTDIR, exist_ok=True)

def swets(L,T):
    """Returns Permeability, diffusivity, or solubility
    of fused Silica in units: mol/cm/s/atm for a given T in Kelvin"""
    if T >= 600:
        DEa = 6613 # factor of 4 to convert from g Helium to moles
        SEa = -1174
        DFF = 7.40E-4
        SFF = 1.28E17
    else:
        DEa = 5580
        SEa = -680
        DFF = 3.04E-4
        SFF = 1.99E17
    D = DFF*np.exp(-DEa/(Rcal*T))
    if L.upper() == 'D':
        return D
    S = SFF*np.exp(-SEa/(Rcal*T)) # K units: atom/cm/s/dP atm/
    if L.upper() == 'S':
        return S
    #print(f"Solubility at T = {T-273}C: {S} atoms/cm3/atm")
    #print(f"Diffusivity at T = {T-273}C: {D} cm2/s")
    #print(f"Permeation at T = {T-273}C in mol/cm/s/atm: {D*S}")
    K = D*S#/6.022E23 #units: mol/cm/s/atm
    if L.upper() == 'K':
        return K
    else:
        raise Exception("function is swets(L,T) where L is one of [D,S,K] for:\nDiffusivity, Solubility, and Permeability")
    
def InvertFrequencyFactor(t, F, Fp): 
    """
    Time in Seconds, F: Cumulative yield of 1, Fp: previous cumulative yield
    EQN 5a-c from Fechtig and Kalbitzer, 1966
    """
    
    if F <= 0.1:
        D_a2 = ((F**2 - Fp**2)*np.pi) / (36*t)
    elif F < 0.9:
        D_a2 = (1/(np.pi**2*t)) * (   (((-(np.pi**2)/3) * (F - Fp))) + ( (-2*np.pi)* (((1-((np.pi/3)*F))**0.5) - ((1-((np.pi/3))*Fp)**0.5) )  )    ) 
    elif F <= 1:
        D_a2 = (1/(np.pi**2*t)) * np.log( (1-Fp)/(1-F) )
    else:
        raise ValueError('Let F be fractional yield, within 0-1')
    return D_a2      

def InvertFrequencyFactor1(ts, Fs): 
    """
    Time in Seconds, F: Cumulative yield of 1, Fp: previous cumulative yield
    EQN 5a-c from Fechtig and Kalbitzer, 1966
    """
    
    Fs = np.array(Fs)
    
    Fps = np.array([0] + Fs[:-1].tolist())
    Fs = np.array(Fs)
    D_a2L = []
    
    for i, F in enumerate(Fs):
        Fp = Fps[i]
        t = ts[i]
        if F <= 0.1:
            D_a2 = ((F**2 - Fp**2)*np.pi) / (36*t)
        elif F < 0.9:
            D_a2 = (1/(np.pi**2*t)) * (   (((-(np.pi**2)/3) * (F - Fp))) + ( (-2*np.pi)* (((1-((np.pi/3)*F))**0.5) - ((1-((np.pi/3))*Fp)**0.5) )  )    ) 
        elif F <= 1:
            D_a2 = (1/(np.pi**2*t)) * np.log( (1-Fp)/(1-F) )
        else:
            raise ValueError('Let F be fractional yield, within 0-1')
        D_a2L.append(D_a2)
        
    return D_a2L

def Forward_Diffuse(Dt_a2):
    """Input is cumulative Dt_a2. 
    Equations 4a-c Fechtig and Kalbitzer, 1966"""
    
    Bt = (np.pi**2) * Dt_a2
    
    F = (6/(np.pi**(3/2))) * (Bt**(1/2)) # Small Yield Approx
    if F > 0.1:
        F = 1 - ((6/(np.pi**2)) * np.exp(-Bt)) # High Yield Approx
    if F < 0.9:
        F =(6/(np.pi**(3/2))) * (Bt**(1/2)) - ((3/(np.pi**2)) * Bt) # Mid-Yield Approx
        
    return F

def Simulate_Diffusion(D0_a2, Ea, T, t, R = 8.314):
    """Let T and t be 1D arrays of equal length describing sequential time-temperature steps,
    T in Celcius and t in minutes
    Let D0_a2 be sec^-1
    Default activation energy units are joules/mol, but R can be changed to match other energy units"""
    if np.shape(T) != np.shape(t) or T.ndim != 1:
        raise ValueError('Let T and t be 1D arrays of equal length describing sequential time-temperature steps')
    
    Dt_a2 = 0
    Fcum = []
    seconds = t*60 # minutes to seconds
    for i, sec in enumerate(seconds):
        K = 273+T[i]
        Dt_a2 +=  ((D0_a2 * np.exp(-Ea/(R*K)) * sec))
        Fcum.append(Forward_Diffuse(Dt_a2))

    return Fcum

Ratoms = 1.3621E-22
Rcal = 1.987

def diffusion_reduction(HeVec, TimeSeconds, TempKelvin = None):

    """Requires vector of measured diffusant in arbitrary units and equal length vector of time in seconds. 
    If temperature given then it will be outputted and plotted in an arrhenius plot
    """

    total_yield = np.sum(HeVec)
    fcum = []
    Fp = 0
    DC_indices = []
    D_a2 = []
    lnD_a2 = []
    blank_corrected_yield = []
    
    for i, step_yield in enumerate(HeVec):
        F = Fp + (step_yield/total_yield)
        frequency_factor = InvertFrequencyFactor(t = TimeSeconds[i], F = F, Fp = Fp)
        D_a2.append(frequency_factor)
        lnD_a2.append(np.log(frequency_factor))
        blank_corrected_yield.append(step_yield)
        DC_indices.append(i)
        fcum.append(F)
        Fp = F

    if np.sum(TempKelvin):
        data = [(TempKelvin-273).tolist(), (TimeSeconds/60).tolist(), HeVec, fcum, D_a2, lnD_a2, (10000/TempKelvin).tolist()]
        columns = ['Temp (C)', 'Time (min)', 'He Yield (nCC@STP)', 'Fcum', 'D/a^2 ', 'ln(D/a^2)', '10^4/T']
        
        #Plotting...
        min_T = np.min(10000/TempKelvin[:-1])
        max_T = np.max(10000/TempKelvin[:-1])
        plt.plot(10000/TempKelvin[:-1], np.array(lnD_a2)[:-1], linestyle='--', marker='o', color='b', label = 'Simulated Encapsulated Apatite')
        plt.title(f"Diffusivity Inversion for Total Yield = {total_yield} ncc's")


        reference_D0_a2 = [(10**1.5)/((150/10000)**2), (10**1.5)/((250/10000)**2), np.exp(1.1939)] # /sec
        reference_Ea = [33000, 33000, 14701*1.987] # cal /mol



        reference_names = ['True Diffusivity of Apatite (a=150 um)', 'DApB 250 um', 'pyrite']
        R = 1.98 #cal /mol /T(K)

        first_only = True
        if len(reference_D0_a2) > 0 and len(reference_D0_a2) == len(reference_Ea):
            T = [min_T, max_T]
            for i, D0_a2 in enumerate(reference_D0_a2):
                if first_only:
                    Ea = reference_Ea[i]
                    min_log_frequency_factor = np.log(D0_a2*np.exp(-Ea/((10000*(min_T**-1))*R)))
                    max_log_frequency_factor = np.log(D0_a2*np.exp(-Ea/((10000*(max_T**-1))*R)))
                    plt.plot(T, [min_log_frequency_factor, max_log_frequency_factor], label = reference_names[i])
                    first_only = False
        #plt.show()

    else:
        data = [(TimeSeconds/60).tolist(), HeVec, fcum, D_a2, lnD_a2]
        columns = ['Time (min)', 'He Yield (nCC@STP)', 'Fcum', 'D/a^2 ', 'ln(D/a^2)']

    Reduced_Data = pd.DataFrame()
    for i, column in enumerate(columns):
        Reduced_Data[column] = data[i]
    return Reduced_Data

def tube_permeate_analytical(T, t, G):
    """ 
    Returns n/n0, fraction of initial Helium remaining within tube after permeation"""
    K = swets('K', T)
    return(np.exp(-(K*Ratoms*T*G*t)))

def tube_permeate_differential(T, G):
    """Returns dn/dt, rate ofchange in atoms of Helium in tube by permeation"""
    K = swets('K', T)
    return(-K*Ratoms*T*G)

Tsched = [200,100,230,100,260,100,290,160,400,200,400,200] 
tsched = [3600,3600,3600,3600,7200,3600,3600,14400,1800,3600,1800,3600]

def Simulate_Diffusion_Tube(D0, a, Ea, T, t, OD, ID, R = 1.987):
    """Let T and t be 1D arrays of equal length describing sequential time-temperature steps,
    T in Kelvin and t in seconds
    Let D0_a2 be sec^-1
    Default activation energy units are joules/mol, but R can be changed to match other energy units"""
    #if np.shape(T) != np.shape(t) or T.ndim != 1:
    #    raise ValueError('Let T and t be 1D arrays of equal length describing sequential time-temperature steps')
    
    total_seconds = np.arange(np.sum(t))
    n0 = []
    n0_ends = []
    m = []
    w = []
    Fstep_apparent = []
    Fcum = []
    Fcum_apparent = []
    Fcum_apparentP = 0
    FP = 0
    Dt_a2 = 0
    n0P = 0 
    t_out = []
    t_outP = 0
    m_cum = []
    measured_cum = 0.0
    outF = 0
    temps = []
    Fsteps = []
    dt = 1.0  # seconds; inner loop is evaluated at 1-second resolution
    #n1HT = [0]
    G = 2/(np.log(OD/ID)*((ID/2)**2))
    for j, tstep in enumerate(t):
        Tk = T[j] + 273
        D = D0*np.exp(-Ea/(R*Tk))
        outF = 0 # collected gas in a single step
        leak_coeff = -tube_permeate_differential(T = Tk, G = G)
        evolved = 0
        for s in np.arange(tstep):
            Dt_a2 += dt * (D/(a**2)) 
            F_step = Forward_Diffuse(Dt_a2) - FP
            evolved += F_step
            w.append(evolved)
            n0.append(F_step+n0P)
            FP += F_step
            Fcum.append(FP)
            # Forward Euler (FDM) update from dn/dt = -leak_coeff * n
            out = leak_coeff * n0[-1] * dt
            n0[-1] -= out
            outF += out
            measured_cum += out
            m_cum.append(measured_cum)
            m.append(outF)
            Fsteps.append(out)
            n0P = n0[-1]
            #n1HT.append(((out-n1HT[-1])/denom)/(1-(1/denom)))
            #n1HT
            temps.append(Tk)
        print(1 - leak_coeff*dt)
        n0_ends.append(n0P)
        Fstep_apparent.append(outF)
        Fcum_apparent.append(outF+Fcum_apparentP)
        Fcum_apparentP = Fcum_apparent[-1]
        t_out.append(t_outP+tstep)
        t_outP = t_out[-1]
        
    return Fcum, n0, Fstep_apparent, Fcum_apparent, n0_ends, t_out, temps, Fsteps, m, w, m_cum

time_input =  [10800,7200,7200,7200,3600, 7200, 7200,7200,7200] #seconds
temp_input = [200,250,300,350,400,325,275,250,175] # celcius

Fcum, n0, Fstep_apparent, Fcum_apparent, n0_ends, t_out, temps, Fsteps, m, w, m_cum = Simulate_Diffusion_Tube(D0 = 10**1.5, a = 150/1E4, T = temp_input, t =time_input, Ea = 33000, OD = 1000/1E4, ID=600/1E4)

plt.plot(np.arange(len(n0))/3600, n0, color = 'black', label = r'$n_t$: $^{He}F$ in tube')
#plt.plot(np.arange(len(n0)), Fsteps, label = 'Apparent Yield (measured)')
#plt.plot(np.arange(len(n0)), Fcum[1:]-Fcum[:-1], label = 'Fractional Yield from Apatite')
#plt.plot(np.array(t_out)/3600, Fcum_apparent, color = 'k', linestyle = '--', label = r'"Measured" $\Sigma ^{He}F$')

cmap = mpl.cm.get_cmap('cool')
norm = mpl.colors.Normalize(vmin=np.min(temp_input), vmax=np.max(temp_input))
mapped_colors = cmap(norm(temp_input))

times = np.arange(len(n0))/3600

# Plot apatite cumulative evolved yield by temperature step.
step_start = 0
for i, step_end in enumerate(t_out):
    label = r'$\omega_{cum}$: Apatite $\Sigma ^{He}F$' if i == 0 else None
    plt.plot(times[step_start:step_end], Fcum[step_start:step_end], color = mapped_colors[i], label = label, linewidth = 3)
    step_start = step_end

# Plot each temperature step as its own colored segment using continuous cumulative measured output.
step_start = 0
for i, step_end in enumerate(t_out):
    plt.plot(times[step_start:step_end], m_cum[step_start:step_end], color = mapped_colors[i], linestyle = '--', linewidth = 2)
    step_start = step_end

#plt.scatter(t_out, n1HT[1:], label = 'Inferred Tube Contents from High Temp')
plt.xlabel('Time (Hours)')
plt.ylabel(r'Fractional Helium Yield $\left(\Sigma\right) ^{He}F$')
plt.scatter(np.array(t_out)/3600, Fcum_apparent, c = temp_input, cmap = 'cool', label = '_nolegend_')

cbar = plt.colorbar()
cbar.set_label('Temperature (°C)')
plt.grid(True)
plt.title('Forward Modeled Helium Step Heat Yields\nfor Encapsulated Durango Apatite')
handles, labels = plt.gca().get_legend_handles_labels()
measured_handle = Line2D([0], [0], color=mapped_colors[0], linestyle='--', marker='o', markersize=6,
                         label=r'$m_{cum}$: Measured $\Sigma ^{He}F$')
plt.legend(handles + [measured_handle], labels + [r'$m_{cum}$: Measured $\Sigma ^{He}F$'],
           fontsize=LEGEND_SIZE * 0.75)  # crowded legend, kept smaller than the standard size
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, 'Durango_Sim.pdf'), dpi=300)#, dpi = 1024)
plt.show()

plt.plot(np.arange(len(n0))/3600, n0, linestyle = '--', color = 'blue',label = r'Fractional Yield in Tube ($n_t$)')
plt.plot(np.arange(len(n0))/3600, m, linestyle = '--', color = 'red', label = r'Measurable Fractional Yield ($m$)')
plt.plot(np.arange(len(n0))/3600, w, color = 'black', label = r'Evolved Fractional Yield ($w$)')
plt.xlabel('Time (hr)')
plt.ylabel(r'Helium Fractional Yield of 150 $\mu$s Durango Apatite')
plt.savefig(os.path.join(OUTDIR, 'Diffusion_Tube_Simulation1.0.pdf'), dpi=300)
plt.show()


diffdat = diffusion_reduction(Fstep_apparent+[1-Fstep_apparent[-1]], TimeSeconds=np.array(time_input+[0]), TempKelvin=np.array(temp_input+[0])+273)
plt.show()

x = diffdat['10^4/T']
y = diffdat['ln(D/a^2)']

['Temp (C)', 'Time (min)', 'He Yield (nCC@STP)', 'Fcum', 'D/a^2 ', 'ln(D/a^2)', '10^4/T']

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()
Ctemps = np.array([100,150,200,250,300,350,400])

xliminp = [160,420]

ax1.plot(x,y,marker = 'o', linestyle = '--', label = '"Measured" Apparent Diffusivities')


xlim = np.array([1E4/(273+xliminp[1]),1E4/(273+xliminp[0])])

ax1.plot(xlim,np.log((10**1.5)/(0.0150**2)*np.exp(-33000/(1.987*10000/xlim))), color = 'red', label = 'True Diffusivity')

ax1.set_xlim(xlim)
#ax1.set_ylim([-35,-9])
#ax1.set_ylim([-32,-17])#[-35,-9])
ax2.set_xticks(1E4/(Ctemps+273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (C)')
ax1.set_xlabel(r'$\frac{10000}{T^{ }(K)}$')
ax1.set_ylabel(r'Apparent Diffusivity $\left(\frac{D}{a^2}\right)$')
#ax1.legend(loc = 'upper right', fontsize = 8)
ax1.grid(True)
ax1.legend()
plt.title('Forward Modeled Apparent Helium Diffusivities\nfor Encapsulated Durango Apatite (r = 150 µm)')
fig.tight_layout()
plt.savefig(os.path.join(OUTDIR, 'Apatite_diff_sim1.1.pdf'), dpi=300)#dpi = 1024)
plt.show()