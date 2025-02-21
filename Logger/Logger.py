import numpy as np
import json
import sys,os
import pickle

from PyQt5.QtCore import QObject, pyqtSignal


__version__='3.1'
__date__='2025.02.21'



class Logger(QObject):
    updated = pyqtSignal()
    path=os.getcwd()
    ZeroPositionFileName=path+'\\ZeroPosition.txt'
    SpectralDataFolder=path+'\\SpectralData\\'
    SpectralBinaryDataFolder=path+'\\SpectralBinData\\'
    TDFolder=path+'\\TimeDomainData\\'
    ParametersFileName=path+'\\Parameters.txt'
    
    S_print=pyqtSignal(str) # signal used to print into main text browser
    S_print_error=pyqtSignal(str) # signal used to print errors into main text browser
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.counter = 0
        self.spectra = None
        self.wavelengths = None
        self.positions = list()
        self.file=None
        self.saving_file_type='bin'



    def save_data(self, Data,name,X,Y,Z,piezo_Z,SourceOfData:str):
        name=name+'_X={}_Y={}_Z={}_piezoZ={:.4f}_'.format(X,Y,Z,piezo_Z)
        if SourceOfData=='FromScope':
            FileName=self.TDFolder+'TD_'+name+'.osc_pkl'
        elif SourceOfData=='FromOSA':
            FileName=self.SpectralDataFolder+'Sp_'+name+'.pkl'
        if self.saving_file_type=='txt':
            np.savetxt(FileName.split('.')[0]+'.txt', Data)
        elif self.saving_file_type=='bin':
            f = open(FileName,"wb")
            pickle.dump(Data,f)
            f.close()
        self.S_print.emit('\nData saved\n')

    def save_parameters(self, list_dictionaries):
        f=open(self.ParametersFileName,'w')
        json.encoder.FLOAT_REPR = lambda x: format(x, '.5f') if (x<0.01) else x
        json.dump(list_dictionaries,f)
        f.close()
        self.S_print.emit('\nParameters saved\n')

    def load_parameters(self):
        '''
        load dictionaries of the parameters from file to dict
        '''
        try:
            f=open(self.ParametersFileName)
            Dicts=json.load(f)
            f.close()
            self.S_print.emit('\nParameters loaded\n')
            return Dicts
        except FileNotFoundError:
            self.S_print_error.emit('Error while load parameters: Parameters file not found')
            return None
        except json.JSONDecodeError:
            self.S_print_error.emit('Errpr while load parameters: file has wrong format')
            return None
        
    
    def save_zero_position(self,X:int,Y:int,Z:int,piezoZ:float):
        Dict={}
        Dict['X_0']=str(X)
        Dict['Y_0']=str(Y)
        Dict['Z_0']=str(Z)
        Dict['piezoZ']=str(piezoZ)
        f=open(self.ZeroPositionFileName,'w')
        json.dump(Dict,f)
        f.close()
        self.S_print.emit('\nzero position saved\n')
        
    def load_zero_position(self):
        try:
            f=open(self.ZeroPositionFileName)
        except FileNotFoundError:
            return 0,0,0,0
        try:
            dictionary=json.load(f)
            f.close()
            return float(dictionary['X_0']),float(dictionary['Y_0']),float(dictionary['Z_0']),float(dictionary['piezoZ'])
        except:
            return 0,0,0,0


    


if __name__ == "__main__":
    logger = Logger()
    logger.savePosition(10,323,0,'54')
    logger.savePosition(10,423,40,'545')
    del logger