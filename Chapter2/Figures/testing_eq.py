import numpy as np
import matplotlib.pyplot as plt
from diffusion_utils import swets, Ratoms

G = 3500
delta = 1.1

def lamT(T, t):
    return G*Ratoms*swets('K',T)*T*t

def fractionate(T, t):

    return (1+(1/(lamT(T, t)-1)))/(1+(1/((delta*lamT(T, t))-1)))

Ts = 500,550,600
t = np.linspace(10,50,1000)
for T in Ts:
    plt.plot(t, fractionate(T, t*3600), label=f'{T-273} °C')
plt.xlabel('Time (hours)')
plt.ylabel('Fractionation from measured')
plt.legend()
plt.show()

G = 3500
delta = 1.1



def fractionate(T, t):
    return (1+(1/(lamT(T, t))))/(1+(1/((delta*lamT(T, t)))))

Ts = 500,550,600
t = np.linspace(10,50,1000)
for T in Ts:
    plt.plot(t, fractionate(T, t*3600), label=f'{T-273} °C')
plt.xlabel('Time (hours)')
plt.ylabel('Fractionation from measured, no -1')
plt.legend()
plt.show()



for T in Ts:
    plt.plot(t, ((delta*lamT(T, t*3600))-1)/((lamT(T, t*3600))-1), label=f'{T-273} °C')
plt.xlabel('Time (hours)')
plt.ylabel('Fractionation from measured')
plt.legend()
plt.show()

for T in Ts:
    plt.plot(t, (delta*lamT(T, t*3600))/(lamT(T, t*3600)), label=f'{T-273} °C')
plt.xlabel('Time (hours)')
plt.ylabel('Fractionation from measured, no -1')
plt.legend()
plt.show()