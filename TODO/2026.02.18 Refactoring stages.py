# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 15:07:44 2026

@author: Илья
"""

class Stages(QObject):
    connected = pyqtSignal()
    stopped = pyqtSignal()
    Stage_key={'X':None,'Y':None,'Z':None}
    abs_position={}
    relative_position={}
    zero_position={'X':0,'Y':0,'Z':0}
    S_print_error=pyqtSignal(str) # signal used to print errors into main text browser
    
    def __init__(self,
                 stage_x=None,
                 stage_y=None,
                 stage_z=None):
        
        self.abs_position['X']=None
        self.abs_position['Y']=None
        self.abs_position['Z']=None
        
        self.zero_position['X']=None
        self.zero_position['Y']=None
        self.zero_position['Z']=None
        
        self.relative_position['X']=None
        self.relative_position['Y']=None
        self.relative_position['Z']=None
        
    
    def _-(self,l):
        '''
        l - это [x_0,y_0, z_0]
        '''
        self.zero_position['X']=l[0]
        self.zero_position['Y']=l[1]
        self.zero_position['Z']=l[2]
        self.update_relative_positions()
    
    def update_relative_positions(self):
        self.relative_position['X']=self.abs_position['X']-self.zero_position['X']
        self.relative_position['Y']=self.abs_position['Y']-self.zero_position['Y']
        self.relative_position['Z']=self.abs_position['Z']-self.zero_position['Z']
        
        
    def shiftOnArbitrary(self, key:str, distance:float):
        '''
        Подвинуть подвижку, ответсвенную за ось key, на distance mkm.
        '''
        device_id=self.Stage_key[key]
        result = move on arbitrary
        self.abs_position[key]=self.get_position(device_id) # запрашиваю новые абсолютные координаты у той подвижки, которая сдвинулась
        self.update_relative_positions()
        self.stopped.emit()
        
    def move_home(self, key=None):
        '''
        пдвинуть в начальное положение те подвижки, у которых есть такая опция
        Обновить их относитльные и абсолютные координаты
        '''
        
        self.abs_position[]=0
        self.update_relative_positions()
        self.stopped.emit()
'''      
Типы подвижек:
     - STANDA - реализовано только для совместно 3 осей в Hardware/Stages/Standa/StandaStages.py
         в первую очерелдь - реализовать упрваление отдельной подвижкой станда
     
     - Thorlabs KCube - реализовано совместно для 2 осей в Hardware/Stages/MyThorlabsStages_2_Cubes.py
     - Thorlabs NRT 100 - Реализовано внутри 2осевого класса в Hardware/Stages/MyThorlabsStages.py
     - LBTEK EM-CV - реализовано нормально для упрваления отдельной подвижкой, но возмонжо надо будет переименовать функции  Hardware/Stages/LBTEK_stage.py
     - PIinstruments реализовао для 3осевого класса в Hardware/Stages/PIStages.py - в последнюю очередь 
 '''