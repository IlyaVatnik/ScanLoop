# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 20:33:15 2025

@author: Илья
"""

__version__='0.1'
__date__='2025.02.20'

class Hardware_ports():
    def __init__(self):
        self.APEX='10.2.60.25'
        self.Yokogawa="10.2.60.60"
        self.scope='10.2.60.176'
        self.scope_Rigol='10.2.60.132'
        self.laser_Pure_Photonics='COM4'
        self.powermeter_serial_number='P0015055'
        self.LUNA=1
        self.interrogator='192.168.19.111'
        self.piezo_stage='COM5'
    
    def set_attributes(self, d:dict):
         for key in d:
             self.__setattr__(key, d[key])



    def get_attributes(self) -> dict:
         '''
         Returns
         -------
         Seriazible attributes of the
         '''
         d = dict(vars(self)).copy()  # make a copy of the vars dictionary
         return d