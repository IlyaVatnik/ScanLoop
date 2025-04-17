# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 10:50:41 2020

@author: Ilya
"""

__version__='2.0'
__date__='2025.03.20'

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
from scipy.fftpack import rfft, irfft, fftfreq
from scipy.signal import find_peaks
import pickle
from Resonances_wavelengths import Resonances
#from ComputingAzimuthalAndRadialModes import Resonances


MinimumPeakDepth=1  ## For peak searching 
MinimumPeakDistance=2 ## For peak searching in points
threshold=0.1


Wavelength_min=1538
Wavelength_max=1556

# FileName=r"C:\Users\Илья\Desktop\Sp_spec2_X=0_Y=0_Z=0_piezoZ=0.1990__resaved.pkl"
# FileName=r"F:\!Projects\!SNAP system\Misc\2025.03 How to distinguish radial numbers\try 5\p 5_resaved.pkl"
# FileName=r"F:\!Projects\!SNAP system\Misc\2025.03 How to distinguish radial numbers\try 2\Sp_temp 29_3 tr4_X=0.0_Y=90.0_Z=0.0_piezoZ=22.9612__resaved.pkl"
FileName=r"F:\!Projects\!SNAP system\Misc\2025.03 How to distinguish radial numbers\MM 50125\Processed_spectrogram_at_-7145.0_resaved.pkl"

R0 = 62.43
range_R=1
n0 = 1.45
p0=15
delta_n = 1e-4
delta_R = 1e-2

T0=25
range_T=30
delta_T = 1

dispersion=True

def get_experimental_data():
    

    
    FilterLowFreqEdge=0.00
    FilterHighFreqEdge=0.01
    def FFTFilter(y_array):
        W=fftfreq(y_array.size)
        f_array = rfft(y_array)
        Indexes=[i for  i,w  in enumerate(W) if all([abs(w)>FilterLowFreqEdge,abs(w)<FilterHighFreqEdge])]
        f_array[Indexes] = 0
    #        f_array[] = 0
        return irfft(f_array)
    with open(FileName,'rb') as f:
        Temp=pickle.load(f)
    Wavelengths_TE=Temp[:,0]
    index_TE_min=np.argmin(abs(Wavelengths_TE-Wavelength_min))
    index_TE_max=np.argmin(abs(Wavelengths_TE-Wavelength_max))
    Signals_TE=FFTFilter(Temp[index_TE_min:index_TE_max,1])
    Wavelengths_TE=Wavelengths_TE[index_TE_min:index_TE_max]
    # Temp=np.loadtxt(FileName2)
    # Wavelengths_TM=Temp[:,0]
    # index_TM_min=np.argmin(abs(Wavelengths_TM-Wavelength_min))
    # index_TM_max=np.argmin(abs(Wavelengths_TM-Wavelength_max))
    # Signals_TM=FFTFilter(Temp[index_TM_min:index_TM_max,1])
    # Wavelengths_TM=Wavelengths_TM[index_TM_min:index_TM_max]
    Wavelengths_TM=0
    Signals_TM=0
    Resonances_TE_indexes,_=find_peaks(-Signals_TE,prominence=MinimumPeakDepth,distance=MinimumPeakDistance,threshold=threshold)
    Resonances_TE_exp=Wavelengths_TE[Resonances_TE_indexes]
    return Wavelengths_TE,Signals_TE,Wavelengths_TM,Signals_TM,Resonances_TE_indexes,Resonances_TE_exp

Wavelengths_TE,Signals_TE,Wavelengths_TM,Signals_TM,Resonances_TE_indexes,Resonances_TE_exp=get_experimental_data()

fig, axs = plt.subplots(2, 1, sharex=True,figsize=(10, 8))
plt.subplots_adjust(left=0.1, bottom=0.3)
axs[0].plot(Wavelengths_TE,Signals_TE)
axs[0].plot(Wavelengths_TM,Signals_TM)
axs[0].plot(Wavelengths_TE[Resonances_TE_indexes],Signals_TE[Resonances_TE_indexes],'.')
axs[0].set_title('N=%d' % len(Resonances_TE_indexes))
plt.sca(axs[1])

resonances=Resonances(Wavelength_min,Wavelength_max,n0,R0*1e3,p0,material_dispersion=dispersion)
tempdict=resonances.__dict__
resonances.plot_all(0,1,'both')
plt.xlim([Wavelength_min,Wavelength_max])

axs[1].set_title('N=%d,n=%f,R=%f,p_max=%d' % (resonances.N_of_resonances['Total'],n0,R0,p0))
#

#s = n0 * np.sin(2 * np.pi * R0 * t)
#l, = axs[1].plot(t, s, lw=2)
#axs[1].margins(x=0)

axcolor = 'lightgoldenrodyellow'
ax_n = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor=axcolor)
ax_R = plt.axes([0.25, 0.15, 0.65, 0.03], facecolor=axcolor)
ax_p = plt.axes([0.25, 0.2, 0.65, 0.03], facecolor=axcolor)
ax_T = plt.axes([0.25, 0.25, 0.65, 0.03], facecolor=axcolor)

s_n = Slider(ax_n, 'n', 1.4, 1.6, valinit=n0, valstep=delta_n)
s_R = Slider(ax_R, 'R', R0-range_R/2, R0+range_R/2, valinit=R0,valstep=delta_R)
s_p = Slider(ax_p, 'p', 1, 15, valinit=p0,valstep=1)
s_T = Slider(ax_T, 'T', 10, 60, valinit=T0,valstep=delta_T)
#axs[1].set_title('N=%d,n=%f,R=%f,p_max=%d' % (Resonances_th.N_of_resonances,best_res['x'][0],best_res['x'][1],p_best))

def update(val):
    n = s_n.val
    R = s_R.val
    p=s_p.val
    T=s_T.val
    axs[1].clear()
    resonances=Resonances(Wavelength_min,Wavelength_max,n,R*1e3,p,material_dispersion=dispersion,temperature=T)    
    plt.sca(axs[1])
    resonances.plot_all(0,1,'both')
    axs[1].set_title('N=%d,n=%f,R=%f, T=%f,p_max=%d' % (resonances.N_of_resonances['Total'],n,R,T,p))
#    plt.xlim([Wavelength_min,Wavelength_max])
#    plt.show()


s_n.on_changed(update)
s_R.on_changed(update)
s_p.on_changed(update)
s_T.on_changed(update)

resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
button = Button(resetax, 'Reset', color=axcolor, hovercolor='0.975')


def reset(event):
    s_n.reset()
    s_R.reset()
    s_p.reset()
button.on_clicked(reset)

#rax = plt.axes([0.025, 0.5, 0.15, 0.15], facecolor=axcolor)
#radio = RadioButtons(rax, ('red', 'blue', 'green'), active=0)
#
#
#def colorfunc(label):
#    l.set_color(label)
#    fig.canvas.draw_idle()
#radio.on_clicked(colorfunc)

plt.show()