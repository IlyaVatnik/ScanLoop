# Hardware/Stages/Thorlabs/thorlabs_stages.py
# -*- coding: utf-8 -*-
__version__ = '1.0'
__date__ = '2026.05.11'

import time
import logging

logger = logging.getLogger(__name__)

KDC_ENCODER_STEP = 0.03
BSM_ENCODER_STEP = 0.002


def get_thorlabs_serials():
    """Сканирует доступные устройства Thorlabs"""
    serials = []
    
    # ← ИМПОРТ ВНУТРИ ФУНКЦИИ (чтобы поймать ошибку DLL)
    try:
        from Hardware.Stages.thorlabs_kinesis import benchtop_stepper_motor as bsm
        from Hardware.Stages.thorlabs_kinesis import KCube_DC_Servo as kdc
    except Exception as e:
        logger.warning(f"[Thorlabs] DLL не найдена: {e}")
        print(f"[Thorlabs] DLL не найдена — сканирование пропущено")
        return serials
    
    try:
        print(">>> Пытаемся сканировать KDC...")
        kdc.TLI_BuildDeviceList()
        
        if hasattr(kdc, 'TLI_GetDeviceListSize'):
            device_count = kdc.TLI_GetDeviceListSize()
            print(f"[Thorlabs] Найдено KDC устройств: {device_count}")
            
            for i in range(device_count):
                if hasattr(kdc, 'TLI_GetDeviceListByType'):
                    serial = kdc.TLI_GetDeviceListByType(i)
                    if serial:
                        serials.append(serial.decode('utf-8'))
    except Exception as e:
        logger.error(f"[Thorlabs] Ошибка сканирования: {e}")
        print(f"[Thorlabs] Ошибка: {e}")
    
    return serials


class ThorlabsAxis:
    def __init__(self, serial_no, axis_type='KDC'):
        # ← ИМПОРТ ВНУТРИ КЛАССА
        try:
            from Hardware.Stages.thorlabs_kinesis import benchtop_stepper_motor as bsm
            from Hardware.Stages.thorlabs_kinesis import KCube_DC_Servo as kdc
        except FileNotFoundError as e:
            raise RuntimeError(f"Thorlabs DLL не найдена: {e}")
        
        from ctypes import c_char_p, c_int, c_short, c_uint
        
        self.serial_no = c_char_p(bytes(serial_no, "utf-8"))
        self.axis_type = axis_type
        self.channel = c_short(0)
        self.milliseconds = c_int(100)
        self.is_connected = False
        self.bsm = bsm
        self.kdc = kdc
        
        if axis_type == 'KDC':
            self.encoder_step = KDC_ENCODER_STEP
            self._init_kdc()
        elif axis_type == 'BSM':
            self.encoder_step = BSM_ENCODER_STEP
            self._init_bsm()
        else:
            raise ValueError(f"Неизвестный тип оси: {axis_type}")

    def _init_kdc(self):
        self.kdc.TLI_BuildDeviceList()
        err = self.kdc.CC_Open(self.serial_no)
        time.sleep(0.1)
        if err == 0:
            logger.info(f"[Thorlabs.KDC] Подключено: {self.serial_no.value.decode()}")
            self.is_connected = True
        else:
            raise RuntimeError(f"Не удалось подключиться к KDC {self.serial_no.value.decode()}")

    def _init_bsm(self):
        self.bsm.TLI_BuildDeviceList()
        err = self.bsm.SBC_Open(self.serial_no)
        time.sleep(0.1)
        if err == 0:
            logger.info(f"[Thorlabs.BSM] Подключено: {self.serial_no.value.decode()}")
            self.is_connected = True
        else:
            raise RuntimeError(f"Не удалось подключиться к BSM {self.serial_no.value.decode()}")

    def get_position(self):
        if self.axis_type == 'KDC':
            pos = int(self.kdc.CC_GetPosition(self.serial_no)) * self.encoder_step
        elif self.axis_type == 'BSM':
            pos = int(self.bsm.SBC_GetPosition(self.serial_no, self.channel)) * self.encoder_step
        return round(pos, 1)

    def move_relative(self, distance_mkm):
        distance_in_steps = int(distance_mkm / self.encoder_step)
        logger.info(f"[Thorlabs] move_relative: {distance_mkm} мкм = {distance_in_steps} шагов")
        
        if self.axis_type == 'KDC':
            self.kdc.CC_StartPolling(self.serial_no, self.milliseconds)
            self.kdc.CC_ClearMessageQueue(self.serial_no)
            time.sleep(0.1)
            self.kdc.CC_SetMoveRelativeDistance(self.serial_no, c_int(distance_in_steps))
            self.kdc.CC_MoveRelativeDistance(self.serial_no)
            time.sleep(0.5)
            self.kdc.CC_StopPolling(self.serial_no)
        elif self.axis_type == 'BSM':
            self.bsm.SBC_StartPolling(self.serial_no, self.channel, self.milliseconds)
            self.bsm.SBC_ClearMessageQueue(self.serial_no, self.channel)
            time.sleep(0.1)
            self.bsm.SBC_SetMoveRelativeDistance(self.serial_no, self.channel, c_int(distance_in_steps))
            self.bsm.SBC_MoveRelativeDistance(self.serial_no, self.channel)
            time.sleep(0.5)
            self.bsm.SBC_StopPolling(self.serial_no, self.channel)

    def move_home(self):
        logger.info(f"[Thorlabs] move_home")
        if self.axis_type == 'KDC':
            self.kdc.CC_StartPolling(self.serial_no, self.milliseconds)
            self.kdc.CC_ClearMessageQueue(self.serial_no)
            self.kdc.CC_Home(self.serial_no)
            time.sleep(2)
            self.kdc.CC_StopPolling(self.serial_no)
        elif self.axis_type == 'BSM':
            self.bsm.SBC_StartPolling(self.serial_no, self.channel, self.milliseconds)
            self.bsm.SBC_ClearMessageQueue(self.serial_no, self.channel)
            self.bsm.SBC_Home(self.serial_no, self.channel)
            time.sleep(2)
            self.bsm.SBC_StopPolling(self.serial_no, self.channel)

    def wait_for_stop(self):
        pass

    def close(self):
        if self.axis_type == 'KDC':
            self.kdc.CC_Close(self.serial_no)
        elif self.axis_type == 'BSM':
            self.bsm.SBC_Close(self.serial_no)
        logger.info(f"[Thorlabs] Закрыто: {self.serial_no.value.decode()}")

    def __del__(self):
        self.close()