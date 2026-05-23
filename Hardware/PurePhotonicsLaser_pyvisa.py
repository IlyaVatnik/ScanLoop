# -*- coding: utf-8 -*-
"""
Created on Sat Dec  3 15:22:02 2022

@author: Илья
Using lib by Artem Kirik and pyvisa

"""


__date__='2022.12.03'

if __name__=='__main__':

    from LaserLibs import itla_pyvisa
else:
    
    from Hardware.LaserLibs import itla_pyvisa
    
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from Utils.Loggable import Loggable

def nmToHz(nm : float):
    return int(299792458 / nm * 1e9)

def dnm_to_dHz(nm:float,d_nm:float):
    return -int(299792458/nm**2*d_nm*1e9)

class Laser(QObject, Loggable):
    S_print=pyqtSignal(str) # signal used to print into main 1text browser
    S_print_error=pyqtSignal(str) # signal used to print errors into main text browser
    def __init__(self,COMPort):
        QObject.__init__(self)
        if type(COMPort)==str and 'COM' in COMPort:
            COMPort=int(COMPort.split('COM')[1])
        try:
            self.itla=itla_pyvisa.PPCL550(COMPort)
            self.log.info("Connected to PPCL550 laser via pyvisa on port %s", COMPort)
        except Exception as e:
            self.log.exception("Failed to connect to PPCL550 laser on port %s", COMPort)
            self.S_print.emit('Error! Not connected')
            pass
        self.maximum_tuning=200.1 # in pm
        self.tuning=0
        self.main_wavelength=1550 # in nm
    
    def setOn(self):
        self.itla.on()
        self.log.info("PPCL550 laser ON")
 
    def setOff(self):
        self.itla.off()
        self.log.info("PPCL550 laser OFF")
    
    def setPower(self,Power): # in 0.01 dB
        self.itla.set_power(int(Power))
        self.log.info("PPCL550 laser power set to %s dBm", Power*0.01)
    
    def setMode(self, ModeKey):
        modes = {
            'dither' : 0,
            'no dither' : 1,
            'whisper' : 2
            }
        error=True
        while error:
            try: 
                self.itla.mode(ModeKey) 
                error=False
                self.log.info("PPCL550 laser mode set to %s", ModeKey)
            except:
                pass
        

    def setWavelength(self, nm: float): # in nm, accuracy: 0.001 nm
        freq = nmToHz(nm)
        self.itla.set_frequency(freq)
        self.main_wavelength=nm
        self.log.info("PPCL550 wavelength set to %s nm", nm)
        return

    def fineTuning(self, pm: float): # in pm, accuracy : 0.01 pm
        if pm<self.maximum_tuning:
            dfreq=dnm_to_dHz(self.main_wavelength, pm*1e-3)
            self.itla.set_FTFrequency(dfreq)
            self.tuning=pm
            self.log.info("PPCL550 fine tuned by %s pm", pm)
        else:
            self.log.error("PPCL550 fineTuning failed: pm=%s > max=%s", pm, self.maximum_tuning)


    
    def state(self):
        super().state()
        self.md = self.ask_value(0x90)
        return self.__dict__


if __name__=='__main__':
    import os
    os.chdir('..')
    # from LaserLibs import itla_pyvisa
    laser=Laser(8)
    laser.setOn()
    laser.setMode('whisper')
    laser.setOff()



