# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 18:11:03 2025

@author: Илья
"""

'''

NOTE that positions are in microns!


'''

__data__='2025.08.12'
__version__='1'

from PyQt5.QtCore import QObject,  pyqtSignal
import sys
import os
import numpy as np
from Hardware.Stages.LBTEK_stage import LBTEK_stage
from Hardware.Stages.StandaStages import StandaStages



class StandaAndLBTekStages(StandaStages):
   
    def __init__(self):
        super().__init__()
        self.LBTek_stage=LBTEK_stage()



    

    def shiftOnArbitrary(self, key:str, distance:float):
        if key=='Z':
            self.LBTek_stage.jog_by(distance)
            self.abs_position[key]=self.LBTek_stage.get_position()
            self.update_relative_positions()
            self.stopped.emit()

        else:
           self.shiftOnArbitrary(key, distance)

#    def shift(self, key:str,Sign_key):
#        device_id=self.Stage_key[key]
#        distance=int(np.sign(Sign_key)*self.StepSize[key])
#        print(distance)
#        result = self.lib.command_movr(device_id, distance, 0)
#        if (result>-1):
#            self.abs_position[key]+=distance
#        print("Result: Shifted - " + str(bool(result+1)))
#        self.stopped.emit()


    def __del__(self):
        super().__del__()
        del self.LBTek_stage

if __name__ == "__main__":
    stages=StandaStages()
    d=5
    # stages.shiftOnArbitrary('X',d)

    del stages

#################################### CLOSE CONNECTION #######################################


