'''
By Alexandr Nesterok
Modified by Ilya
Using serial interface
'''
__version__='3.2'
__date__='2025.04.17'


import serial


if __name__=='__main__':
    from LaserLibs import ITLA_serial as ITLA
else:
    from Hardware.LaserLibs import ITLA_serial as ITLA
import numpy as np

from PyQt5.QtCore import pyqtSignal, QObject
from Utils.Loggable import Loggable

def nmToDGHz(nm : float):
    return int(299792458 / nm * 10)

# class Metaclass_Serial(serial.Serial.__class__):
#     pass
# class Metaclass_QObject(QObject.__class__):
#     pass

# class MultiMetaclass(Metaclass_Serial, Metaclass_QObject):
#     pass

class Laser(QObject, Loggable):
    
 
    S_print=pyqtSignal(str) # signal used to print into main 1text browser
    S_print_error=pyqtSignal(str) # signal used to print errors into main text browser

    
    def __init__(self,COMPort):
        QObject.__init__(self)
        self.port=serial.Serial(port=COMPort,
                                baudrate=9600,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE,
                                bytesize=serial.EIGHTBITS,
                                timeout = 0.4)
        # QObject.__init__(self)
        ITLA.ITLAConnect(COMPort)
        self.maximum_tuning=200.1 # in pm
        self.tuning=0
        self.main_wavelength=0 # in nm
        # print('Connected to laser using Serial module')
        self.S_print.emit('Connected to laser using Serial module')
        self.log.info("Connected to laser on %s", COMPort)


    def setOn(self):
        res=ITLA.ITLA(self.port, ITLA.REG_Resena, 8, ITLA.WRITE)
        self.S_print.emit('Laser is on')
        self.log.info("Laser ON")
        return res

    def setOff(self):
        res=ITLA.ITLA(self.port, ITLA.REG_Resena, 0, ITLA.WRITE)
        self.S_print.emit('Laser is off')
        self.log.info("Laser OFF")
        return res
    
    def setPower(self,Power): # in 0.01 dB
        res=ITLA.ITLA(self.port, ITLA.REG_Power, Power, ITLA.WRITE)
        self.S_print.emit('Laser power is changed')
        self.log.info("Laser power set to %s", Power)
        return res
    
    def setMode(self, ModeKey):
        ModeKeys={
                'dither':0,
                'no dither':1,
                'whisper':2}
        Command=ModeKeys[ModeKey]
        
        res=ITLA.ITLA(self.port, ITLA.REG_Mode, Command, ITLA.WRITE)
        self.S_print.emit('Laser mode is changed')
        self.log.info("Laser mode set to %s", ModeKey)
        return res

    def setWavelength(self, nm: float): # in nm, accuracy: 0.001 nm
        freq = nmToDGHz(nm)
        THz = freq // 10000
        dGHz = freq % 10000
        ITLA.ITLA(self.port, ITLA.REG_Fcf1, THz, ITLA.WRITE)
        ITLA.ITLA(self.port, ITLA.REG_Fcf2, dGHz, ITLA.WRITE)
        self.main_wavelength=nm
        self.S_print.emit('Laser wavelength is changed')
        self.log.info("Laser wavelength set to %s nm", nm)
        return

    def fineTuning(self, pm: int): # in pm, accuracy : 0.01 pm
        if pm<self.maximum_tuning:
            C = 299792458
            THz = ITLA.ITLA(self.port, ITLA.REG_Lf1, 0, ITLA.READ)
            dGHz = ITLA.ITLA(self.port, ITLA.REG_Lf2, 0, ITLA.READ)
            l1 =  C / (THz + (dGHz * 10 ** (-4)))
            df = -1 * C * pm / (l1 * (l1 + pm))
            dfe = df * (10 ** (6))
            self.tuning=pm
            res= ITLA.ITLA(self.port, ITLA.REG_Ftf, np.uint16(dfe), ITLA.WRITE)
            self.S_print.emit('Laser is fine tuned')
            self.log.info("Laser fine tuned by %s pm", pm)
            return res
        else:
            self.S_print_error.emit('Laser is off')
            self.log.error("fineTuning failed: pm=%s > max_tuning=%s", pm, self.maximum_tuning)



if __name__=='__main__':
    laser=Laser('COM6')
    # laser.setOn()
    # laser.setOff()
    del laser



