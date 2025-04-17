# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 23:56:09 2022


@author: t-vatniki

Estimate different mode parameters:
    - Threshold for nonlinear Kerr effects
    - Mode amplitude under given pump rate AND
    - Change of the temperature of the cavity under pumping
    


Estimations given following М. Л. Городецкий, Оптические Микрорезонаторы с Гигантской Добротностью (2012).
"""

__version__='5'
__date__='2025.03.28'

import numpy as np
from scipy import special
import matplotlib.pyplot as plt 
from Field_distributions import get_V_jj,get_Veff,get_cross_section

delta_c=4e6 # 2*pi*Hz
delta_0=8e6 # 2*pi*Hz
lambda_0=1550 # nm


length=20 # micron
R=110 #micron
delta_theta=1 # s^-1, thermal dissipation time, (11.35) from Gorodetsky, calculated numerically
m=355
p=1
pol='TE'



P_in=0.05 # W
'''
'''
C_2=1.5e4 # micron/microsec
Im_D=5.1e4 # micron/microsec
Gamma=10 # 1/microsec
# w=32 # micron, gussian distribution
a=433 # micron, maximum position

'''


'''





n=1.445
c=3e8 #m/sec
n2=3.2e-20 #m**2/W


# absorption=6.65e12/4.343 * np.exp(-52.62/(lambda_0*1e-3))/1e6 # 1/m, after (10.7) Gorodetsky
# absorption=1e-3*1e2
# absorption=5e-4*1e2 # 1/m
absorption=0.028 # 1/m

epsilon_0=8.85e-12 # F/m
int_psi_4_by_int_psi_2=0.7 # for gaussian distribution
specific_heat=680 # J/kg/K
density=2.2*1e3 # kg/m**3

delta_omega=0

hi_3=4*n2/3*epsilon_0*c*n**2
omega=c/(lambda_0*1e-9)*2*np.pi # 1/sec



    
def F(delta_c,length,R): # NOTE that definition follows Gorodetsky, not Kolesnikova 2023
    return np.sqrt(4*P_in*delta_c/(epsilon_0*n**2*volume(length,R)))  #(11.21) 

def get_field_intensity(delta_c,length,R):
    field_intensity=F(delta_c,length,R)**2/(delta_c+delta_0)**2 # (from first diff equation in 11.20)
    return field_intensity


def Kerr_threshold_gorodetski(wavelength,delta_c,delta_0,volume_jj):
    '''
    volume_jj in m^3
    
    delta_c : in 1/mks.
    delta_0 : in 1/mks
    
    wavelength, nm
    '''
    omega=c/(wavelength*1e-9)*2*np.pi # 1/sec
    delta=(delta_0+delta_c)
    thres=n**2*volume_jj*delta**3/c/omega/n2/delta_c # Gorodecky (11.25)
    return thres

def Kerr_threshold(wave,delta_c,delta_0,length,R):
    '''
    
    Parameters
    ----------
    wave : TYPE
        DESCRIPTION.
    delta_c : in 1/mks.
    delta_0 : in 1/mks
    length : in mkm
    R : in mkm

    Returns
    -------
    thres : in W

    '''
    omega=c/(lambda_0*1e-9)*2*np.pi # 1/sec
    delta=((delta_0+delta_c))
    thres=n**2*volume(length,R)*np.power(delta,3,dtype = np.float64)/c/omega/n2/delta_c # Kolesnikova 2023
    return thres


def get_heat_effect(delta_c,delta_0,length,R):
    zeta=epsilon_0*n*c*absorption*get_cross_section(R)/(2*specific_heat*density*np.pi*R_0**2*1e-12)
    heat_effect=get_field_intensity(delta_c,length,R)*zeta/delta_theta/P_in    
    temperature_shift=get_field_intensity(delta_c,length,R)*zeta/delta_theta*int_psi_4_by_int_psi_2
    return heat_effect,temperature_shift

def get_min_threshold(R,wave,potential_center,potential_width,C2,ImD,Gamma):
    '''
    potential_width in microns
    potential_center in microns 
    C2 in micron/mks
    ImD in micron/mks
    Gamma in 1/mks
    '''
    omega=c/(lambda_0*1e-9)*2*np.pi # 1/sec
    Leff=np.sqrt(2*np.pi)*potential_width*1e-6 # integral INtensity(z) dz, m
    Leff_2=np.sqrt(2*np.pi)*potential_width/np.sqrt(2)*1e-6 # integral INtensity(z)**2 dz, m
    min_threshold=9*epsilon_0*n**4/omega/hi_3*(Gamma*1e6)**2*(ImD)/C2*(get_cross_section(R)*Leff)**2 / (get_cross_section_2(R)*Leff_2)
    optimal_position=potential_center-np.sqrt(-(np.log(Gamma*Leff*1e6/2/ImD)*2*w**2)) # in microns
    return min_threshold, optimal_position # in W, in micron

if __name__=='__main__':
    
    delta=delta_c+delta_0
    volume_jj=get_V_jj(R,length,m,p,pol)
    threshold=Kerr_threshold_gorodetski(lambda_0,delta_c,delta_0,volume_jj)
    # heat_effect,temperature_shift=get_heat_effect(delta_c,delta_0,length,R_0)
    # min_threshold, position=get_min_threshold(R_0,omega,a,w,C_2,Im_D,Gamma)
    
    print('Threshold for Kerr nonlinearity={} W'.format(threshold))
    print('Cross section={:.3e} mkm^2, volume={:.3e} mkm^3, v_jj={:.3e} mkm^3'.format(get_cross_section(R,m,p,pol)*1e12,get_Veff(R, length, m,p,pol)*1e18,get_V_jj(R, length, m,p,pol)*1e18))
    # print('Minimal Threshold at optimized point={} W'.format(min_threshold))
    print('Q_factor={:.2e}'.format(omega/delta))
    # print('Mode amplitude squared={:.3e} (V/m)**2'.format(get_field_intensity(delta_c,length,R_0)))
    # print('Thermal shift {} K '.format(temperature_shift))
    # print('Averaged temperature response is {} degrees per Watt of pump'.format(heat_effect))
    
    #%%
 