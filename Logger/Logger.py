# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 20:33:15 2025
@author: Илья
"""

__version__='3.3'
__date__='2026.03.30'

import numpy as np
import json
import sys, os
import pickle
from PyQt5.QtCore import QObject, pyqtSignal


class Logger(QObject):
    # ✅ СИГНАЛЫ — СТРОГО НА УРОВНЕ КЛАССА (до __init__, без self!)
    updated = pyqtSignal()
    S_print = pyqtSignal(str)
    S_print_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ ПУТИ — вычисляем при создании экземпляра
        self.path = os.getcwd()
        self.ZeroPositionFileName = self.path + '\\ZeroPosition.txt'
        self.SpectralDataFolder = self.path + '\\SpectralData\\'
        self.SpectralBinaryDataFolder = self.path + '\\SpectralBinData\\'
        self.TDFolder = self.path + '\\TimeDomainData\\'
        self.ParametersFileName = self.path + '\\Parameters.txt'

        self.counter = 0
        self.spectra = None
        self.wavelengths = None
        self.positions = list()
        self.file = None
        self.saving_file_type = 'bin'

    def save_data(self, Data, name, X, Y, Z, piezo_Z, SourceOfData: str):
        name = name + '_X={}_Y={}_Z={}_piezoZ={:.4f}_'.format(X, Y, Z, piezo_Z)
        if SourceOfData == 'FromScope':
            FileName = self.TDFolder + 'TD_' + name + '.osc_pkl'
        elif SourceOfData == 'FromOSA':
            FileName = self.SpectralDataFolder + 'Sp_' + name + '.pkl'
        if self.saving_file_type == 'txt':
            np.savetxt(FileName.split('.')[0] + '.txt', Data)
        elif self.saving_file_type == 'bin':
            f = open(FileName, "wb")
            pickle.dump(Data, f)
            f.close()
        self.S_print.emit('\nData saved\n')
    
    def save_parameters(self, list_dictionaries):
        # ✅ ПРОВЕРЯЕМ путь перед записью
        self.S_print.emit(f'\nSaving parameters to: {self.ParametersFileName}\n')
        
        try:
            # ✅ Создаём папку если не существует
            os.makedirs(os.path.dirname(self.ParametersFileName), exist_ok=True)
            
            f = open(self.ParametersFileName, 'w', encoding='utf-8')
            json.encoder.FLOAT_REPR = lambda x: format(x, '.5f') if (x < 0.01) else x
            json.dump(list_dictionaries, f, indent=2, ensure_ascii=False)
            f.close()
            self.S_print.emit('\nParameters saved\n')
        except Exception as e:
            import traceback
            self.S_print_error.emit(f'\nError saving parameters: {e}\n')
            self.S_print_error.emit(traceback.format_exc())
            

    def load_parameters(self):
        try:
            f = open(self.ParametersFileName)
            Dicts = json.load(f)
            f.close()
            self.S_print.emit('\nParameters loaded\n')
            return Dicts
        except FileNotFoundError:
            # ✅ Это НЕ ошибка, просто файла нет
            return None
        except json.JSONDecodeError:
            self.S_print_error.emit('Error while load parameters: file has wrong format')
            return None
    
    def save_zero_position(self, X: int, Y: int, Z: int, piezoZ: float):
        Dict = {}
        Dict['X_0'] = str(X)
        Dict['Y_0'] = str(Y)
        Dict['Z_0'] = str(Z)
        Dict['piezoZ'] = str(piezoZ)
        f = open(self.ZeroPositionFileName, 'w')
        json.dump(Dict, f)
        f.close()
        self.S_print.emit('\nzero position saved\n')
        
    def load_zero_position(self):
        try:
            f = open(self.ZeroPositionFileName)
        except FileNotFoundError:
            return 0, 0, 0, 0
        try:
            dictionary = json.load(f)
            f.close()
            return float(dictionary['X_0']), float(dictionary['Y_0']), float(dictionary['Z_0']), float(dictionary['piezoZ'])
        except:
            return 0, 0, 0, 0