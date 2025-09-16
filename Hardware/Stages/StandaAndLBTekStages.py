# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 18:11:03 2025

@author: Илья
"""

'''

NOTE that positions are in microns!


'''

__data__='2025.09.16'
__version__='1.3'



if __name__ != '__main__':
    from Hardware.Stages.LBTEK_stage import LBTEK_stage
    from Hardware.Stages.Standa.StandaStages import StandaStages
else:
    from LBTEK_stage import LBTEK_stage
    from Standa.StandaStages import StandaStages

LBTek_stage_key='Y'
LBTek_stage_min_position=0
LBTek_stage_max_position=30000 # mkm

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
        self.update_relative_positions()
        self.stopped.emit()

    def shiftOnArbitrary(self, key:str, distance:float):
        if key==LBTek_stage_key:
            # new_position=round(self.LBTek_stage.get_position()+distance) 
            '''
            опрос позиции _перед_ тем, как сдвинуть подвижку - вынужденная мера, поскольку по невыясненным причинам в обрятном порядке эти две функции не работают
            Испробованы добавления пауз
            '''
            current_pos=self.abs_position[LBTek_stage_key]
            if (current_pos+distance>LBTek_stage_min_position) & (current_pos+distance<LBTek_stage_max_position):
                self.LBTek_stage.jog_by(distance)
                self.abs_position[LBTek_stage_key]=self.LBTek_stage.get_position()
                self.update_relative_positions()
                self.stopped.emit()
            else:
                self.S_print_error.emit('Error: destination position exceeds the maximum allowed to LBTek stage')

        else:
            device_id=self.Stage_key[key]
            self.lib.command_movr(device_id, int(distance/2.5), 0)
    #        if (result>-1):
            self.lib.command_wait_for_stop(device_id, 11)
            self.abs_position[key]=self.get_position(device_id)
            self.update_relative_positions()
            self.stopped.emit()



    def __del__(self):
        super().__del__()
        del self.LBTek_stage
#%%
if __name__ == "__main__":
    s=StandaAndLBTekStages()
    s.move_home()
    distance=1000
    s.shiftOnArbitrary('Y',distance)
    s.LBTek_stage.get_position()
    s.LBTek_stage.move_home()


#################################### CLOSE CONNECTION #######################################


