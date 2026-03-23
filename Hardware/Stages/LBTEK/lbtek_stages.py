# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 14:42:03 2026

@author: Александр
"""

"""
Файл: Hardware/Stages/LBTEK/lbtek_stages.py
"""
import time
import ctypes
from ctypes import c_int, c_float, c_char_p, POINTER
from pathlib import Path
from threading import Lock

try:
    # Для Windows (путь вычисляется автоматически относительно этого файла)
    module_dir = Path(__file__).parent.absolute()
    dll = ctypes.CDLL(str(module_dir / "LBTEKx64" / "MoverLibrary.dll"))
except Exception as e:
    print(f"Ошибка при загрузке библиотеки LBTEK: {e}")
    dll = None
    
class LimitPositionException(Exception):
    pass

# ====================================================================
# ВАШ ОРИГИНАЛЬНЫЙ КЛАСС (Без изменений)
# ====================================================================
class LBTEK_stage:
    min_position=-15000
    max_position=15000 # mkm
    
    def __init__(self, serial_no=None):
        self.id=1 # номер оси 
        
        if serial_no==None:
            serial_buffer = c_char_p(b' ' * 1024)
            result = dll.listPorts(serial_buffer, 1024)
            port_list=serial_buffer.value.decode('utf-8')
            for port in port_list.split(','):
                self.serial_no = port.encode('utf-8')
                self.handle = dll.openEmcvx(self.serial_no)
                if self.handle > 0:
                    if dll.isOpen(self.serial_no):
                        if self.init_axis(1, "EM-LSS65-30C1", 1) == 0:
                            print("Устройство EM-CV2-1 открыто")
                            break
        else:
            self.serial_no = serial_no.encode('utf-8')
            self.handle = dll.openEmcvx(self.serial_no)
            if self.handle <= 0:
                raise Exception("Не удалось открыть устройство")
            if self.init_axis(1, "EM-LSS65-30C1", 1) == 0:
                print("Ось инициализирована успешно")
                
        self._dll_lock = Lock()
        dll.GetCurrentPos.restype = c_float
        dll.setJogTime.argtypes = [c_int, c_int, c_int]
        dll.setJogStep.argtypes = [c_int, c_int, c_float]
        dll.getJogStep.restype = c_float
        dll.getErrorCode.restype = c_int
        
        self.jog_step=self.get_jog_step() # in mkm
        self.set_axis_enable(1,0) #/1- выключить ось  , 0 -включить

    def __del__(self):
        if dll and hasattr(self, 'handle'):
            dll.closeEmcvx(self.handle)

    def move_home(self, id=1):
        result=dll.moveEmcvx(self.handle, id, 0x02)
        self.wait_until_idle()  
        return result
    
    def jog_pos(self, id=1):
        return dll.moveEmcvx(self.handle, id, 0x07)
        
    def jog_neg(self, id=1):
        return dll.moveEmcvx(self.handle, id, 0x08)                                     
    
    def set_jog_step(self,step,id=1 ):
        self.jog_step=step
        return dll.setJogStep(self.handle, id, step/1e3)
    
    def get_jog_step(self, id=1):
        return dll.getJogStep(self.handle, id)*1e3

    def get_position(self, id=1):
        Error=True
        while Error:
            try:
                result=dll.GetCurrentPos(self.handle, id)*1e3
                Error=False
            except OSError:
                pass
        return round(result, 2) # Округляем до 2 знаков для красоты
            
    def set_axis_enable(self,enable, id=1 ):
        return dll.setAxisEnable(self.handle, id, enable)

    def get_doing_state(self, id=1):
        return dll.getDoingState(self.handle, id)

    def wait_until_idle(self, id=1, timeout=15.0, check_interval=0.05):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.get_doing_state(id) == 0:
                return True
            time.sleep(check_interval)
        return False

    def jog_by(self,step,id=1):
        current_pos=self.get_position()
        if (current_pos+step>self.min_position) & (current_pos+step<self.max_position):
            if self.jog_step!=abs(step):
                self.set_jog_step(abs(step))
            if step>0:
                self.jog_pos()
            elif step<0:
                self.jog_neg()
            self.wait_until_idle()
        else:
            raise LimitPositionException('Error: Limit position would be exceeded')

    def init_axis(self, id, model, axis_count):
        model_bytes = model.encode('utf-8')
        result = dll.initAxis(self.handle, id, model_bytes, axis_count)
        if result != 0:
            raise Exception(f"Ошибка инициализации оси: {result}")
        return result


# ====================================================================
# АДАПТЕР ДЛЯ НАШЕГО МЕНЕДЖЕРА СТАНДАРТНЫХ ОСЕЙ
# ====================================================================
class LBTEKAxis:
    """
    Обертка, которая делает интерфейс LBTEK точно таким же, как у Standa.
    """
    def __init__(self, identifier):
        # Если передан пустой ID (None) - ищем автоматически
        self.stage = LBTEK_stage(serial_no=identifier)

    def get_position(self):
        return self.stage.get_position()

    def move_relative(self, distance_mkm):
        self.stage.jog_by(distance_mkm)

    def move_home(self):
        self.stage.move_home()

    def wait_for_stop(self):
        # jog_by и move_home уже ждут остановки, но метод оставим для совместимости
        self.stage.wait_until_idle()

    def close(self):
        self.stage.__del__()