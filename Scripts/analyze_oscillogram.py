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

__version__ = '0.3'
__date__ = '2025.02.28'

def Lorenz(det_f,non_resonant_transmission,X_0,delta_c,delta_0,phi):
    delta_freq=det_f-X_0
    
    transmission=non_resonant_transmission*np.abs( np.exp(1j*phi*np.pi)-2*delta_c/( (delta_0+delta_c+1j*delta_freq) ) )**2
    return transmission

def fit_Lorenz(Det,Y,func,p0,detuning_range):
    
    popt, pcov=curve_fit(func,Det,Y,p0,bounds=(0, [10,detuning_range*2*np.pi, detuning_range, detuning_range,detuning_range]))
    round_n=3
    popt=np.round(popt,round_n)
    return popt


def cut_wave(X,Y,dith_frequency):
    dittering_Period=1/dith_frequency
    ind_left=np.where(abs(X+dittering_Period*3.2)<1e-7)[0]
    ind_right=np.where(abs(X-dittering_Period*3.2)<1e-7)[0]
    #print('ind_left',ind_left[0])
    #print('ind_right',ind_right[0])
    X=X[ind_left[0]:ind_right[0]]
    Y=Y[ind_left[0]:ind_right[0]]
    return X,Y,ind_left[0]

def find_Pigs(X,Y):
    N=len(X)
    Pig_array=np.array([])
    I_Pig=np.array([])
    Peak_moment=np.array([])
    
    Y_min=np.min(Y)
    Y_threshold=1-(1-np.min(Y))/2
    #print('Y_threshold',Y_threshold)
    new_Pig=0#
    i_previous=0
    for i in range(0,N):
        
        if Y[i]<Y_threshold or i==N-1:
            #print('i',i)
            if (i-i_previous>300 and i_previous!=0) or i==N-1:# проверяем перескочили ли мы на следующий пик - большой скачок по индексу
                #print(i-i_previous)
                new_Pig=1
            if new_Pig==1:# это значит, что мы перескочили на другой пик, массив X_Pig содержит времена  предыдущего пика
                #найдем время центра предыдущего пика
                #print(I_Pig)
                Peak_moment=np.append(Peak_moment,int(np.mean(I_Pig))) #запомнили положение пика index!
                
                I_Pig=np.array([])
                new_Pig=0# продолжим работать над пиком
                
            if new_Pig==0:
                #print('w')
                i_previous=i
                I_Pig=np.append(I_Pig,i)
                
    return Peak_moment

def give_detuning(dittering_frequency,detuning,Time):
    ramp=1
    sinus=0
    Time=Time-Time[0]
    if ramp==1:
        Det=Time*detuning*dittering_frequency*2# половина периода только 
    if sinus==1:
        Det=detuning*np.sin(dittering_frequency*Time*2)
    return Det

def get_curve(X,Y, peak_number,dith_frequency,noise_level,detuning):
    # X,Y,index_shift=cut_wave(X,Y,dith_frequency)
    
    # Peak_moment=find_Pigs(X,Y)
    Y-=noise_level
    
    Peak_moment=find_peaks((abs((Y-np.max(Y))/np.max(Y))),prominence=0.4)[0]
    # print(np.min(np.diff(Peak_moment)))
    
    # plt.plot(X[Peak_moment],Y[Peak_moment],'o')
    Detuning_points=[ int(m) for m in ( (Peak_moment[1:]+Peak_moment[:-1])/2 )]
    Det=give_detuning(dith_frequency,detuning,X[Detuning_points[peak_number-1]:Detuning_points[peak_number]]) 
    Signal=Y[Detuning_points[peak_number-1]:Detuning_points[peak_number]]
    # Signal-=noise_level
    #Signal=Signal
    return Det,Signal,Peak_moment[peak_number]#+index_shift

def analyze_oscillogram(X,Y,noise_level,dith_frequency,detuning_range): #x,Y = массив напряжения и времени,
    #get_data(way,amount_to_aver,step)
    peak_number=2 # номер пика в осциллограмме, который булем анализировать
    
    Det,Signal,index_of_peak=get_curve(X,Y, peak_number,dith_frequency,noise_level,detuning_range) #поулчаем пропускание через 1 резонанс,

    
    # plt.plot(Det,Signal)
    Det=Det*2*np.pi # получаем обратные микросекунды
    # center0=Det[np.where(Signal==min(Signal))][0] #сдвигаем центр пика в ноль
    # Det=Det-center0
    
    #print(center0)n
    p0= 1,1,1,1,1#splitted_Lorenz(nonresonant_transmission, det_f,X_0,delta_c,delta_0,g)
    popt_Lor=fit_Lorenz(Det,Signal,Lorenz,p0,detuning_range)
    
    nonresonant_transmission,x0,delta_c,delta_0,phi=popt_Lor
    #axSKO.legend(loc='upper left')
    return  nonresonant_transmission,x0,delta_c,delta_0,phi,index_of_peak # deltas in mks^-1

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
    
