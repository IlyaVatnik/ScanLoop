# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 11:14:45 2025

@author: Аркаша
"""
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path 
from scipy.optimize import curve_fit
import pickle
from scipy.constants import pi
from scipy.constants import c
from scipy.signal import find_peaks
from scipy.signal import savgol_filter

__version__ = '0.5'
__date__ = '2025.03.06'

def Lorenz(det_f,non_resonant_transmission,X_0,delta_c,delta_0,phi):
    delta_freq=det_f-X_0
    
    transmission=non_resonant_transmission*np.abs( np.exp(1j*phi*np.pi)-2*delta_c/( (delta_0+delta_c+1j*delta_freq) ) )**2
    return transmission

def fit_Lorenz(Det,Y,func,p0,detuning_range):
    
    popt, pcov=curve_fit(func,Det,Y,p0,bounds=(0, [10,detuning_range*2*np.pi, detuning_range, detuning_range,detuning_range]))
    round_n=3
    popt=np.round(popt,round_n)
    return popt


def give_detunings(dittering_frequency,detuning,Time):
    ramp=1
    sinus=0
    Time=Time-Time[0]
    if ramp==1:
        Det=Time*detuning*dittering_frequency*2# половина периода только 
    if sinus==1:
        Det=detuning*np.sin(dittering_frequency*Time*2)
    return Det*2*np.pi # в обратные микросекунды

def get_range_to_fit(Y, peak_number,prominence,distance):
    
    Peak_moments=find_peaks((abs((Y-np.max(Y))/np.max(Y))),prominence=prominence,distance=distance)[0]
    Detuning_points=[ int(m) for m in ( (Peak_moments[1:]+Peak_moments[:-1])/2 )]
    
    return Detuning_points[peak_number-1],Detuning_points[peak_number],Peak_moments[peak_number],Peak_moments#,+index_shift

def analyze_oscillogram(times,signal,peak_number,noise_level,dith_frequency,detuning_range,prominence): #x,Y = массив напряжения и времени,
    # номер пика в осциллограмме, который булем анализировать
    max_peak_width=30 #MHz
    
    
    distance=int(max_peak_width/(2*dith_frequency*detuning_range)/(times[1]-times[0]))
    index_start,index_stop,index_of_peak,Peak_moments=get_range_to_fit(signal, peak_number,prominence,distance) #поулчаем пропускание через 1 резонанс,
    detunings=give_detunings(dith_frequency,detuning_range,times[index_start:index_stop])  
    
    p0= 1,1,1,1,1#splitted_Lorenz(nonresonant_transmission, det_f,X_0,delta_c,delta_0,g)
    popt_Lor=fit_Lorenz(detunings,signal[index_start:index_stop]-noise_level,Lorenz,p0,detuning_range)
    
    nonresonant_transmission,x0,delta_c,delta_0,phi=popt_Lor
    return  index_start,index_stop,nonresonant_transmission,x0,delta_c,delta_0,phi,index_of_peak, Peak_moments # deltas in mks^-1

if __name__=='__main__':
    dith_frequency=888 # Hz
    noise_level=0.007 # V
    tuninge_range=80 # MHz
    
    
    tuning_coeff=2*np.pi*tuninge_range*2*dith_frequency
    
    def lorenz_fit(times,non_res_transmission, Fano_phase, time0, delta_0, delta_c):
        delta_0/=tuning_coeff
        delta_c/=tuning_coeff
        return(non_res_transmission*np.abs( np.exp(1j*phi*np.pi)-2*delta_c/( (delta_0+delta_c+1j*(time0-times)) ) )**2)+noise_level
      
        
    import pickle
    file=r"F:\!Projects\!SNAP system\!Python Scripts, Numerics\ScanLoop\TimeDomainData\TD_3_X=0_Y=0_Z=0_piezoZ=0.0000_.osc_pkl"
    with open(file, 'rb') as f:
        data=pickle.load(f)
    times, signal=data[:,0],data[:,1]
    import matplotlib.pyplot as plt
    plt.plot(times, signal)
    nonresonant_transmission,X0,delta_c,delta_0,phi,index_of_peak=analyze_oscillogram(times,signal,noise_level,dith_frequency,tuninge_range)
    print(nonresonant_transmission,X0,delta_c,delta_0,phi)
    time0=times[index_of_peak]
    signal_fitted = lorenz_fit(times, nonresonant_transmission, phi, time0, delta_0, delta_c)
    plt.plot(times,signal_fitted,color='green')
    
