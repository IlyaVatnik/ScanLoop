
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  4 15:01:59 2025

@authors: Аркаша, Ilya
"""

__version__ = '1'
__date__ = '2025.08.12'



import time
import ctypes
from ctypes import c_int, c_float, c_char_p, POINTER
import struct
# Загружаем библиотеку
from pathlib import Path
try:
    # Для Windows
    module_dir = Path(__file__).parent.absolute()
    dll = ctypes.CDLL(str(module_dir / "LBTEKx64" / "MoverLibrary.dll"))

    # Для Linux
    # dll = ctypes.CDLL('libMoverLibrary.so')

except Exception as e:
    print(f"Ошибка при загрузке библиотеки: {e}")
    

# Пример использования
class LBTEK_stage:
    '''
    This is for EM-CV2-1 controller
    
    '''
    
    def __init__(self, serial_no=None):
        
        if serial_no==None:
            # Создаем буфер для списка портов
            serial_buffer = c_char_p(b' ' * 1024)
            
            # Получаем список портов
            result = dll.listPorts(serial_buffer, 1024)
            port_list=serial_buffer.value.decode('utf-8')
            # print(f"Список портов: {serial_buffer.value.decode('utf-8')}")
            for port in port_list.split(','):
                self.serial_no = port.encode('utf-8')  # Преобразуем строку в bytes
                self.handle = dll.openEmcvx(self.serial_no)
                if self.handle > 0:
                    if dll.isOpen(self.serial_no):
                        break
                
        else:
            self.serial_no = serial_no.encode('utf-8')  # Преобразуем строку в bytes
            self.handle = dll.openEmcvx(self.serial_no)
            if self.handle <= 0:
                raise Exception("Не удалось открыть устройство")
            
        if dll.isOpen(self.serial_no):
            print("Устройство EM-CV2-1 открыто")
        else:
            print("Устройство закрыто")
            
        dll.GetCurrentPos.restype = c_float
        dll.setJogTime.argtypes = [c_int, c_int, c_int]
        dll.setJogStep.argtypes = [c_int, c_int, c_float]
        dll.setJogDelay.argtypes = [c_int, c_int, c_int]
        dll.getJogDelay.argtypes = [c_int, c_int]
        dll.getJogDelay.restype = c_int
        dll.getJogStep.argtypes = [c_int, c_int]
        dll.getJogStep.restype = c_float
        dll.getJogTime.argtypes = [c_int, c_int]
        dll.getJogTime.restype = c_int
        dll.setSpeed.argtypes = [c_int, c_int, c_float]
        dll.setSpeed.restype = c_int
        dll.setAcceleration.argtypes = [c_int, c_int, c_float]
        dll.setAcceleration.restype = c_int
        dll.getSpeed.argtypes = [c_int, c_int]
        dll.getSpeed.restype = c_float  # Указываем, что возвращается float
        dll.getAcceleration.argtypes = [c_int, c_int]
        dll.getAcceleration.restype = c_float  # Указываем, что возвращается float
        dll.getErrorCode.argtypes = [c_int, c_int]
        dll.getErrorCode.restype = c_int
        
        self.jog_step=self.get_jog_step() # in mkm
        self.set_axis_enable(1,0) #/1- выключить ось  , 0 -включить
        '''
        Включена первая ось! 
        '''
        self.id=1 # номер оси 
        print(f"Статус оси: {self.get_axis_enable_status(1)}")
        if self.init_axis(1, "EM-LSS65-30C1", 1) == 0: #EM-LSS65-30C1 #EM-CV2-1
            print("Ось инициализирована успешно")
        else:
            raise Exception("Ошибка инициализации оси")
            
   
    
    def __del__(self):
        dll.closeEmcvx(self.handle)

    def move_code_stop(self, id=1): #MOVE_CODE_STOP      0x01
        return dll.moveEmcvx(self.handle, id, 0x01)
    def move_home(self, id=1): #MOVE_CODE_RESTORE   0x02    // вернуться к истокам
        return dll.moveEmcvx(self.handle, id, 0x02)
    def move_code_driver_r(self, id=1): #MOVE_CODE_DRIVE_R   0x04    // positive direction 
        return dll.moveEmcvx(self.handle, id, 0x04)
    def move_code_driver_l(self, id=1): #MOVE_CODE_DRIVE_L   0x05    // negative direction 
        return dll.moveEmcvx(self.handle, id, 0x05)  
    def move_code_move(self, id=1): #MOVE_CODE_MOVE      0x06    // shift to the particular point
        return dll.moveEmcvx(self.handle, id, 0x06)
    def jog_pos(self, id=1):  # MOVE_CODE_JOG_R     0x07    // шаг в позитивном направлении
        return dll.moveEmcvx(self.handle, id, 0x07)
    def jog_neg(self, id=1): #MOVE_CODE_JOG_L     0x08    // шаг в отрицательном направлении                
        return dll.moveEmcvx(self.handle, id, 0x08)                                     
                             
    
    def set_jog_time(self, time,id=1 ): # 设置步进时间
        #dll.setJogTime.restype = c_float
        
        return dll.setJogTime(self.handle, id, time)       
    
    
    def set_jog_step(self,step,id=1 ):# 设置步进步长
        #dll.setJogStep.restype = c_float
        '''
        step is in mkm!! 
        '''
        self.jog_step=step
        return dll.setJogStep(self.handle, id, step/1e3)
    
    def set_jog_delay(self,delay,id=1):
         #dll.setJogStep.restype = c_float

         return dll.setJogDelay(self.handle, id, delay) #设置步进延迟
     
    def get_jog_delay(self, id=1):
        """Получить текущую задержку JOG (в мс)"""

        return dll.getJogDelay(self.handle, id)

    def get_jog_step(self, id=1):
        """Получить текущий шаг JOG (в мкм)"""
      
        return dll.getJogStep(self.handle, id)*1e3

    def get_jog_time(self, id=1):
        """Получить текущее время JOG (в мс)"""
     
        return dll.getJogTime(self.handle, id)
    
    
    def set_speed(self,speed, id=1):
        """Установка скорости (в мм/с или градусах/с)"""
        speed_result=dll.setSpeed(self.handle, id, c_float(speed))
         
        if speed_result == 0:
            print("Скорость установлена успешно")
        else:
            print(f"Ошибка установки скорости: {speed_result}")
        
    
    def set_acceleration(self, acceleration,id=1):
        """Установка ускорения (в мм/с² или градусах/с²)"""
        return dll.setAcceleration(self.handle, id, c_float(acceleration))

        
       
    def get_speed(self, id=1):
        """Получить текущую скорость"""
      
        return dll.getSpeed(self.handle, id)

    def get_acceleration(self, id=1):
        """Получить текущее ускорение"""
      
        return dll.getAcceleration(self.handle, id)
    
    def set_absolute_disp(self, displacement,id=1 ):
        return dll.setAbsoluteDisp(self.handle, id, displacement)
    
    def get_absolute_disp(self, id=1):
        return dll.getAbsoluteDisp(self.handle, id)
    
    def get_position(self, id=1):
        # Предполагаем, что функция возвращает float
        # in mkm! 
        return dll.GetCurrentPos(self.handle, id)*1e3
            
    def setInputEnable(self, enabled,id=1): 
            dll.setInputEnable(self.handle, id, enabled)
            
    def setOutputEnable(self, enable,id=1):
            dll.setOutputEnable(self.handle, id, enable) 

    def read_data(self, data, length):
        """Чтение данных"""
        return dll.readEmcvx(self.handle, data, length)

    def write_data(self, data, length):
        """Запись данных"""
        return dll.writeEmcvx(self.handle, data, length)

    def set_relative_disp(self, disp,id=1 ):
        """Установить относительное смещение"""
        return dll.setRelativeDisp(self.handle, id, disp)

    def get_relative_disp(self, id=1):
        """Получить относительное смещение"""
        return dll.getRelativeDisp(self.handle, id)

    def set_axis_enable(self,enable, id=1 ):
        """Включить/выключить ось"""
        return dll.setAxisEnable(self.handle, id, enable)

    def set_relative_pos_enable(self,enable, id=1 ):
        """Включить/выключить относительное позиционирование"""
        return dll.setRelativePosEnable(self.handle, id, enable)

    def get_doing_state(self, id=1):
        """Получить состояние движения"""
        return dll.getDoingState(self.handle, id)

    def get_positive_limit_enable(self, id=1):
        """Получить статус положительного предела"""
        return dll.getPositiveLimitEnable(self.handle, id)

    def get_negative_limit_enable(self, id=1):
        """Получить статус отрицательного предела"""
        return dll.getNegativeLimitEnable(self.handle, id)

    def get_origin_enable(self, id=1):
        """Получить статус возврата в исходное положение"""
        return dll.getOriginEable(self.handle, id)

    def get_device_code(self):
        """Получить код устройства"""
        return dll.getDeviceCode(self.handle)

    def get_axis_type(self, id=1):
        """Получить тип оси"""
        return dll.getAxisType(self.handle, id)

    def get_input_enable(self, id=1):
        """Получить статус входного сигнала"""
        return dll.getInputEnable(self.handle, id)

    def get_output_enable(self, id=1):
        """Получить статус выходного сигнала"""
        return dll.getOutputEnable(self.handle, id)

    def get_axis_enable_status(self, id=1):
        """Получить статус включения оси"""
        return dll.getAxisEnable(self.handle, id)

    def get_relative_pos_enable_status(self, id=1):
        """Получить статус относительного позиционирования"""
        return dll.getRelativePosEnable(self.handle, id)
    
    def get_error_code(self, id=1):
        """
        Получить код ошибки для указанной оси
        Возвращает:
            int: Код ошибки (0 = нет ошибки)
        9025- нужно перезапустить
        """
        # Настройка типов аргументов и возвращаемого значения
        return dll.getErrorCode(self.handle, id)
        
    def jog_by(self,step,id=1):
        if self.jog_step!=abs(step):
            self.set_jog_step(abs(step))
        if step>0:
            self.jog_pos()
        elif step<0:
            self.jog_neg()
      
        

    
    def get_all_models(self):
        """Получить все модели"""
        model_buffer = c_char_p(b' ' * 1024)
        dll.getAllModels(model_buffer, 1024)
        return model_buffer.value.decode('utf-8')

    def init_axis(self, id, model, axis_count):
        # Преобразуем строку модели в байты
        model_bytes = model.encode('utf-8')
    
        # Вызываем функцию инициализации оси
        result = dll.initAxis(
            self.handle,    # дескриптор устройства
            id,             # идентификатор оси
            model_bytes,    # модель устройства
            axis_count      # количество осей
            )
    
        if result != 0:
            raise Exception(f"Ошибка инициализации оси: {result}")
        return result
    
    #%%
# Пример работы с устройством
if __name__ == "__main__":
    s=LBTEK_stage('Com3')
    s.get_speed()
    # stage.set_jog_step(1)
    # stage.get_jog_delay()
    # stage.get_absolute_disp()
    s.move_home()    
    # # stage.set_jog_step(100)
    # # stage.
    # stage.jog_pos()
