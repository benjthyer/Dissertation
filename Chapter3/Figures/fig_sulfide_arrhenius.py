import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

All_sheets = pd.read_excel('data/plotable_sulfides.xlsx', sheet_name = None)

fig = plt.figure()
ax1 = fig.add_subplot(111)
ax2 = ax1.twiny()
Ctemps = np.array([100,150,200,250,300,350,400,500,600])

phase = ['Pyrite','Pyrite','Pyrite','Pyrite (4He)','Arsenopyrite','Galena','Chalcopyrite']
marker = ['o','o','o','o','s','X','v']


for i, (name, sheet) in enumerate(All_sheets.items()):
    #ax1.plot(xlim, np.log(((10**1.5)/(0.015**2))*np.exp(-33000/(1.987*(273+np.array([420,80]))))), label = 'Farley, 2000 Durango Apatite, r = 150 µm', color = 'green')
    #if 'LVCO' in name or "Rust" in name:
    errors = sheet[['LB Δln(d/a^2)','UB Δln(d/a^2)']].to_numpy().T
    # LB/UB are meant to be non-negative magnitudes (distance below/above the
    # point), but the upstream reduction occasionally yields small negative
    # values right near zero. Clip those to 0 rather than dropping the point --
    # errorbar tolerates NaN (Excel's blank cells) by simply not drawing that
    # whisker, so only the negative values need clipping.
    errors = np.clip(errors, 0, None)
    ax1.errorbar(sheet['10000/TK'],sheet['ln(d/a^2)'],yerr = errors, marker = marker[i] , capsize = 5, alpha = 0.6, linestyle = ':', label = f"{phase[i]}: {name}")

xlim = ax1.get_xlim()
ax1.plot(xlim, np.log(((10**1.5)/(0.015**2))*np.exp(-33000*np.array(xlim)/(1.987*10000))), label = 'Durango Apatite, r = 150 µm', color = 'black')

ax1.set_xlim(xlim)
ax2.set_xticks(1E4/(Ctemps+273))
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticklabels(Ctemps)
ax2.set_xlabel('Temperature (C)')
ax1.set_xlabel(r'$\frac{10000}{T^{ }(K)}$')
ax1.set_ylabel(r'$ln\left(\frac{D}{a^2}\right) \left(sec^{-1}\right)$')
#ax1.legend(loc = 'upper right', fontsize = 8)
ax1.grid()
ax1.legend(fontsize = 7, loc = 'lower right')
plt.title('Irradiated Encapsulated Sulfide 3He Apparent Diffusivity Compilation')
fig.tight_layout()
plt.savefig('generated/Sulfide_compilation_Arr.pdf', dpi = 256)
plt.show()

