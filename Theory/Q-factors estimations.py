# -*- coding: utf-8 -*-
"""
Городецкий М.Л. Оптические микрорезонаторы с гигантской добротностью. 2012. стр. 290

"""

import numpy as np


wavelength=1.57 # mkm
n_water=1.3
n=1.55
sigma_water=2*1e-4 # mkm 
alpha_water=13*1e-4 # 1/mkm


R=200 # mkm

K=(n**2-1)*R/2/sigma_water/n_water**2
Q_water=K*2*np.pi*n_water/alpha_water/wavelength/2.5 # 10.1364/OL.35.002385 , Q-factor for cylinder is  2.5 times smaller


print('Q_water={:.2e}'.format(Q_water))

# #TE 
# K=2.8 
# P=1


# #TM
K=9.6 
P=1/n**2


B=500*1e-3 # mkm
sigma=1.7*1e-3 # mkm

Q_surface=2*K/(K+1)*3*wavelength**3*R/(16*n*np.pi**3*B**2*sigma**2*P**2)/2.5 # for cylinder

print('Q_surface={:.2e}'.format(Q_surface))