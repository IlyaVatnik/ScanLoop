   
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 16:30:03 2020
@author: Ilya Vatnik
matplotlib 3.4.2 is needed! 
"""
__version__='10.1'
__date__='2022.07.07'

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

import pickle
import bottleneck as bn
from scipy import interpolate
import scipy.signal
from  scipy.ndimage import center_of_mass
from scipy.fftpack import rfft, irfft, fftfreq
import scipy.optimize
from numba import njit
# from mpl_toolkits.mplot3d import Axes3D

lambda_to_nu=125e3 #MHz/nm
lambda_to_omega=lambda_to_nu*2*np.pi 

class SNAP():
    def __init__(self,
                 positions=None,
                 wavelengths=None,
                 transmission=None,
                 R_0=62.5):
        
        self.R_0=R_0 # in microns!
        self.refractive_index=1.45
        self.wavelengths=wavelengths
        self.transmission=transmission
        self.positions=None # whole three dimensions, in microns!
        self.axes_dict={'X':0,'Y':1,'Z':2,'W':3,'p':4}
        self.transmission_scale='log'
        self.axis_key='Z'
        
        self.mode_wavelengths=None
        
        if transmission is not None:
            self.lambda_0=np.min(wavelengths)
        else:
            self.lambda_0=None
            
        self.fig_spectrogram=None
        self.date='_'

        

    
    def remove_nans(self):
        indexes_of_nan=list()
    
    def convert_to_lin_transmission(self):
        self.transmission_scale='lin'
        self.transmission=10**((self.transmission-np.max(self.transmission))/10)
    
    def load_ERV_estimation(self,file_name):
        A=np.loadtxt(file_name)
        x_ERV=A[:,0]
        Waves=A[:,1]
        lambda_0=np.nanmin(Waves)
        ERV=(Waves-lambda_0)/np.nanmean(Waves)*self.R_0*1e3
    
        if (max(np.diff(x_ERV))-min(np.diff(x_ERV)))>0:
            f = interpolate.interp1d(x_ERV, ERV)
            x_ERV=np.linspace(min(x_ERV),max(x_ERV),len(x_ERV))
            ERV=f(x_ERV)
        return x_ERV,ERV,lambda_0

    def find_modes(self,prominence_factor=2):
        T_shrinked=np.nanmean(abs(self.transmission-np.nanmean(self.transmission,axis=0)),axis=1)
        mode_indexes,_=scipy.signal.find_peaks(T_shrinked,prominence=prominence_factor*bn.nanstd(T_shrinked))
        mode_wavelengths=np.sort(self.wavelengths[mode_indexes])
        mode_wavelengths=np.array([x for x in mode_wavelengths if x>self.lambda_0])
        self.mode_wavelengths=mode_wavelengths
        return mode_wavelengths
    
    
    
    def find_center(self):
        x=self.positions[:,self.axes_dict[self.axis_key]]
        if self.mode_wavelengths is None:
            self.find_modes()
        ind=np.where(self.wavelengths==np.max(self.mode_wavelengths))[0][0]
        t_f=np.sum(self.transmission[ind-2:ind+2,:],axis=0)
        return (np.sum(t_f*x)/np.sum(t_f))
    
    
    def apply_FFT_filter(self,LowFreqEdge=0.00001,HighFreqEdge=0.001):
        def FFTFilter(y_array):
            W=fftfreq(y_array.size)
            f_array = rfft(y_array)
            Indexes=[i for  i,w  in enumerate(W) if all([abs(w)>LowFreqEdge,abs(w)<HighFreqEdge])]
            f_array[Indexes] = 0
#            f_array[] = 0
            return irfft(f_array)
        for ii,spectrum in enumerate(np.transpose(self.transmission)):
            self.transmission[:,ii]=FFTFilter(spectrum)
    

      

    
    


    # @numba.njit
    def extract_ERV(self,number_of_peaks_to_search=1,min_peak_level=1,min_peak_distance=10000,min_wave=0,max_wave=1e4,find_widths=True,
                    N_points_for_fitting=100,iterate_different_N_points=False,max_N_points_for_fitting=100,iterating_cost_function_type='linewidth',window_width=0.1):
        '''
        analyze 2D spectrogram
        return position of several first (higher-wavelegth) main resonances. Number of resonances is defined by number_of_peaks_to_search
        return corresponding ERV in nm, and resonance parameters:
            nonresonance transmission, Fano phase shift [-pi:pi], depth/width, linewidth
        for each slice along position axis
        
        uses scipy.find_peak
        
        N_points_for_fitting - part of spectrum to be used for fitting. if 0, whole spectrum is used
        iterate_different_N_points - whether to check different N_points_for_fitting in each fitting process
        '''
        
               
        
        NumberOfWavelength,Number_of_positions = self.transmission.shape
        WavelengthArray=self.wavelengths
        x=self.positions[:,self.axes_dict[self.axis_key]]
        number_of_spectral_points=len(WavelengthArray)
        
        PeakWavelengthArray=np.empty((Number_of_positions,number_of_peaks_to_search))
        PeakWavelengthArray.fill(np.nan)
        
        resonance_parameters_array=np.empty((Number_of_positions,number_of_peaks_to_search,8))
        resonance_parameters_array.fill(np.nan)       
        temp_signal=abs(self.transmission-np.nanmean(self.transmission))
        
        for Zind,Z in enumerate(range(0,Number_of_positions)):
        # for Zind,Z in enumerate(range(Number_of_positions-1,-1,-1)):
            if Zind==0:
                peak_indexes,_=scipy.signal.find_peaks(temp_signal[:,Z],height=min_peak_level,distance=min_peak_distance)
                peak_indexes=peak_indexes.astype('float')
                peak_indexes=np.extract((WavelengthArray[peak_indexes.astype('int')]>min_wave) & (WavelengthArray[peak_indexes.astype('int')]<max_wave),peak_indexes)
            
                # peak_indexes=-np.sort(-peak_indexes) ##sort in wavelength decreasing
                peak_indexes=peak_indexes[np.argsort(temp_signal[peak_indexes.astype('int'),0])] ##sort in resonanse dip
            
                if len(peak_indexes)>0:
                    if len(peak_indexes)>=number_of_peaks_to_search:
                        peak_indexes=peak_indexes[:number_of_peaks_to_search]
                    elif len(peak_indexes)<number_of_peaks_to_search:
                        print(number_of_peaks_to_search-len(peak_indexes))
                        peak_indexes=np.hstack((peak_indexes,np.nan*np.zeros(number_of_peaks_to_search-len(peak_indexes))))
                else:
                    print('no peaks found at start position')
            
                peak_indexes=np.sort(peak_indexes) ##sort in wavelength decreasing
                window_indexes=[]
                for i,p in enumerate(peak_indexes):
                    if not np.isnan(peak_indexes[i]):   
                        if i>0:
                            ind_min=int(peak_indexes[i]-(peak_indexes[i]-peak_indexes[i-1])*window_width)
                        else:
                            ind_min=0
                        if i<len(peak_indexes)-1:
                            ind_max=int(peak_indexes[i]+(peak_indexes[i+1]-peak_indexes[i])*window_width)
                        else:
                            ind_max=-1
                    window_indexes.append([ind_min,ind_max])
                        
                    
                
                
            elif Zind!= 0:
                previous_peak_indexes = np.copy(peak_indexes) # Создаю массив с индексами предыдущих пиков
                for i,p in enumerate(peak_indexes):
                    print('Z={},p={}'.format(Z,p))
                    try:
                        if i>0:
                            ind_min=int(peak_indexes[i]-(peak_indexes[i]-peak_indexes[i-1])*window_width)
                        else:
                            ind_min=0
                        if i<len(previous_peak_indexes)-1:
                            ind_max=int(peak_indexes[i]+(peak_indexes[i+1]-peak_indexes[i])*window_width)
                        else:
                            ind_max=-1
                        window_indexes[i]=[ind_min,ind_max]
                    except:
                        pass
                    temp_peak_indexes,_=scipy.signal.find_peaks(temp_signal[window_indexes[i][0]:window_indexes[i][1],Z],height=min_peak_level,distance=min_peak_distance)
                    if len(temp_peak_indexes)>0:
                        peak_indexes[i]=-np.sort(-temp_peak_indexes)[0]+window_indexes[i][0] ##sort in wavelength decreasing
                    else:
                        peak_indexes[i]=np.nan

            

            for ind in range(number_of_peaks_to_search):
                if not np.isnan(peak_indexes[ind]):
                    PeakWavelengthArray[Z,ind]=WavelengthArray[int(peak_indexes[ind])]
            
            
            if find_widths:
                for ii,peak_wavelength in enumerate(PeakWavelengthArray[Z]):
                    if not np.isnan(peak_wavelength):
                        [non_res_transmission,Fano_phase,res_wavelength,depth,linewidth,delta_c,delta_0,N_points_for_fitting]=find_width(WavelengthArray, self.transmission[:,Z], 
                                                                                                                          peak_wavelength,N_points_for_fitting,iterate_different_N_points,max_N_points_for_fitting,
                                                                                                                          iterating_cost_function_type)
                                                                                                                       
                        resonance_parameters_array[Z,ii]=([non_res_transmission,Fano_phase,res_wavelength,
                                                              depth,linewidth,delta_c,delta_0,N_points_for_fitting])
                        # except:
                        #     print('error while fitting')
        lambdas_0=np.nanmin(PeakWavelengthArray,axis=0)
        ERV=(PeakWavelengthArray-lambdas_0)/lambdas_0*self.R_0*self.refractive_index*1e3 # in nm
        
        print('Analyzing finished')


                # self.fig_spectrogram_ERV_lines.append[line]

        
        resonance_parameters_array=np.array(resonance_parameters_array)

   
        
        return x,np.array(PeakWavelengthArray),np.array(ERV),resonance_parameters_array

# @njit
def find_width(waves,signal,peak_wavelength,N_points_for_fitting=0,iterate_different_N_points=False,max_N_points_for_fitting=100,iterating_cost_function_type='linewidth'):
    index=np.argmin(np.abs(waves-peak_wavelength))
    number_of_spectral_points=np.shape(waves)[0]
    if not iterate_different_N_points:
        if N_points_for_fitting==0:
            fitting_parameters,_,_,_=get_Fano_fit(waves, signal,peak_wavelength)
        else:
            i_min=0 if index-N_points_for_fitting<0 else index-N_points_for_fitting
            i_max=number_of_spectral_points-1 if index+N_points_for_fitting>number_of_spectral_points-1 else index+N_points_for_fitting
            fitting_parameters,_,_,_=get_Fano_fit(waves[i_min:i_max], signal[i_min:i_max],peak_wavelength)
    else:
        N_points_for_fitting=10
        minimal_linewidth=np.max(waves)-np.min(waves)
        minimal_err=1000
        error=0
        for N_points in np.arange(10,max_N_points_for_fitting,2):
             i_min=0 if index-N_points<0 else index-N_points
             i_max=number_of_spectral_points-1 if index+N_points>number_of_spectral_points-1 else index+N_points
             fitting_parameters,_,_,_=get_Fano_fit(waves[i_min:i_max], signal[i_min:i_max],peak_wavelength)
             [transmission,phase,peak_wavelength,delta_0,delta_c]=fitting_parameters
             linewidth=(delta_0+delta_c)*2/lambda_to_nu
             
             
             if iterating_cost_function_type=='linewidth':
                 if minimal_linewidth>linewidth:
                     minimal_linewidth=linewidth
                     N_points_for_fitting=N_points
             
             elif iterating_cost_function_type=='net error':
                 error = np.sum(np.abs(10**(Fano_lorenzian(waves[i_min:i_max], *fitting_parameters)/10) - 10**(signal[i_min:i_max])/10))/N_points
                 if minimal_err>error:
                     minimal_err=error
                     minimal_linewidth=linewidth
                     N_points_for_fitting=N_points
             else:
                 print('wrong cost function')
                 return
             if (N_points%10==0): print('N_points={},linewidth={},error={}'.format(N_points,linewidth,error))
             

                 
        i_min=0 if index-N_points_for_fitting<0 else index-N_points_for_fitting
        i_max=number_of_spectral_points-1 if index+N_points_for_fitting>number_of_spectral_points-1 else index+N_points_for_fitting
        fitting_parameters,_,_,_=get_Fano_fit(waves[i_min:i_max], signal[i_min:i_max],peak_wavelength)
    [non_res_transmission, Fano_phase, res_wavelength,delta_0,delta_c]=fitting_parameters
    
    linewidth=(delta_0+delta_c)*2/lambda_to_omega
    depth=4*delta_0*delta_c/(delta_0+delta_c)**2
    return [non_res_transmission,Fano_phase, res_wavelength, depth,linewidth,delta_c,delta_0,N_points_for_fitting]

# @njit
def get_Fano_fit(waves,signal,peak_wavelength=None):
    '''
    fit shape, given in log scale, with 
    Lorenzian 10*np.log10(abs(transmission*np.exp(1j*phase*np.pi) - 1j*2*delta_c/(1j*(w0-w)+delta_0+delta_c))**2)  
    Gorodetsky, (9.19), p.253
    
    may use peak_wavelength
    return [transmission, Fano_phase, resonance_position,delta_0,delta_c], [x_fitted,y_fitted]
    
    '''
    signal_lin=10**(signal/10)
    transmission=np.mean(signal_lin)
    if peak_wavelength is None:
        peak_wavelength=waves[scipy.signal.find_peaks(signal_lin-transmission)[0][0]]
        peak_wavelength_lower_bound=0
        peak_wavelength_higher_bound=np.inf
    else:
        peak_wavelength_lower_bound=peak_wavelength-2e-3
        peak_wavelength_higher_bound=peak_wavelength+2e-3
    
    delta_0=30 # MHz
    delta_c=50 # MHz
    phase=0.0
    
    initial_guess=[transmission,phase,peak_wavelength,delta_0,delta_c]
    bounds=((0,-1,peak_wavelength_lower_bound,0,0),(1,1,peak_wavelength_higher_bound,np.inf,np.inf))
    
    try:
        popt, pcov=scipy.optimize.curve_fit(Fano_lorenzian,waves,signal,p0=initial_guess,bounds=bounds)
        return popt,pcov, waves, Fano_lorenzian(waves,*popt)
    except RuntimeError as E:
        pass
        print(E)
        return initial_guess,0,waves,Fano_lorenzian(waves,*initial_guess)
    
    # @njit
def get_complex_Fano_fit(waves,signal,peak_wavelength=None,height=None):
    '''
    fit shape, given in lin scale, with  complex Lorenzian 
    Gorodetsky, (9.19), p.253
    
    may use peak_wavelength
    return [transmission, Fano_phase, resonance_position,delta_0,delta_c], [x_fitted,Re(y_fitted),Im(y_fitted)]
    
    '''
    signal_abs=np.abs(signal)
    transmission=np.mean(signal_abs)
    
    if peak_wavelength is None:
        indexes=scipy.signal.find_peaks(signal_abs-transmission,height=height)
        print(indexes)
        peak_wavelength=waves[indexes[0][0]]

    peak_wavelength_lower_bound=peak_wavelength-1e-3
    peak_wavelength_higher_bound=peak_wavelength+1e-3
    
    delta_0=300 # MHz
    delta_c=50 # MHz
    total_phase=0
    fano_phase=0.0
    
    initial_guess=[transmission,total_phase,fano_phase,peak_wavelength,delta_0,delta_c]
    bounds=((0,-1,-1,peak_wavelength_lower_bound,0,0),(1,1,1,peak_wavelength_higher_bound,np.inf,np.inf))
    
    re_im_signal=np.hstack([np.real(signal),np.imag(signal)])
    
    try:
        popt, pcov=scipy.optimize.curve_fit(complex_Fano_lorenzian_splitted,np.hstack([waves,waves]),re_im_signal,p0=initial_guess,bounds=bounds)
        return popt,pcov, waves, complex_Fano_lorenzian(waves,*popt)
    except RuntimeError as E:
        pass
        print(E)
        return initial_guess,0,waves,Fano_lorenzian(waves,*initial_guess)

def complex_Fano_lorenzian_splitted(w,transmission,total_phase, fano_phase,w0,delta_0,delta_c):
    N=len(w)
    w_real = w[:N//2]
    w_imag = w[N//2:]
    y_real = np.real(complex_Fano_lorenzian(w_real,transmission,total_phase, fano_phase,w0,delta_0,delta_c))
    y_imag = np.imag(complex_Fano_lorenzian(w_imag,transmission,total_phase, fano_phase,w0,delta_0,delta_c))
    return np.hstack([y_real,y_imag])
    
def complex_Fano_lorenzian(w,transmission,total_phase,fano_phase,w0,delta_0,delta_c):
    '''
    delta_0, delta_c is in 2pi*MHz or 1e6/s
    '''
    return np.exp(1j*total_phase*np.pi)*(transmission*np.exp(1j*fano_phase*np.pi) - 2*delta_c/(-1j*(w0-w)*lambda_to_omega+(delta_0+delta_c)))
     
    
@njit
def Fano_lorenzian(w,transmission,phase,w0,delta_0,delta_c,scale='log'):
    '''
    return log of Fano shape

    Modified formula (9.19), p.253 by Gorodetsky
    w is wavelength
    delta_0, delta_c is in 2pi*MHz or 1e6/s
    '''
    
    return 10*np.log10(np.abs(transmission*np.exp(1j*phase*np.pi) - 2*delta_c/(1j*(w0-w)*lambda_to_omega+(delta_0+delta_c)))**2) 

if __name__ == "__main__":
    '''
    testing and debug
    '''

    #%%
    import os
    import time
    import pickle
    import matplotlib.pyplot as plt
    os.chdir('..')
    
    f='ProcessedData\\dump_data_resaved.SNAP'
    with open(f,'rb') as file:
        Snap=pickle.load(file)
    
    Temp=Snap.extract_ERV(find_widths=False)    
    
