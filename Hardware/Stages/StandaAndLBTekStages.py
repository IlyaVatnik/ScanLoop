# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 18:11:03 2025

@author: Илья
"""

'''

NOTE that positions are in microns!


'''

__data__='2025.08.13'
__version__='1'

from PyQt5.QtCore import QObject,  pyqtSignal
import sys
import os
import numpy as np

if __name__ != '__main__':
    from Hardware.Stages.LBTEK_stage import LBTEK_stage
    from Hardware.Stages.Standa.StandaStages import StandaStages
else:
    from LBTEK_stage import LBTEK_stage
    from Standa.StandaStages import StandaStages

LBTek_stage_key='Y'

class StandaAndLBTekStages(StandaStages):
   
    def __init__(self):
        '''
        Подвижка LBTek пишется _поверх_подвижки
        '''
        super().__init__()
        self.LBTek_stage=LBTEK_stage()
        



    def move_home(self):
        self.LBTek_stage.move_home()
        self.abs_position[LBTek_stage_key]=0

    def shiftOnArbitrary(self, key:str, distance:float):
        if key==LBTek_stage_key:
            new_position=round(self.LBTek_stage.get_position()+distance) 
            '''
            опрос позиции _перед_ тем, как сдвинуть подвижку - вынужденная мера, поскольку по невыясненным причинам в обрятном порядке эти две функции не работают
            Испробованы добавления пауз
            '''
            
            self.LBTek_stage.jog_by(distance)
            self.abs_position[key]=new_position
            self.update_relative_positions()
            self.stopped.emit()

        else:
            device_id=self.Stage_key[key]
            result = self.lib.command_movr(device_id, int(distance/2.5), 0)
    #        if (result>-1):
            self.lib.command_wait_for_stop(device_id, 11)
            self.abs_position[key]=self.get_position(device_id)
            self.update_relative_positions()
            self.stopped.emit()



    def __del__(self):
        super().__del__()
        del self.LBTek_stage

if __name__ == "__main__":
    s=StandaAndLBTekStages()
    # d=5
    s.move_home()
    s.shiftOnArbitrary('Z',500)



#################################### CLOSE CONNECTION #######################################


