# Hardware/Stages/Thorlabs/thorlabs_stages.py
# -*- coding: utf-8 -*-
__version__ = '1.0'
__date__ = '2026.05.11'

import os
import sys
import time
import logging
from ctypes import c_int, c_short, c_char_p, c_uint

logger = logging.getLogger(__name__)

def _kinesis_paths():
    """Возвращает список возможных путей к Kinesis DLL."""
    paths = [
        r"C:\Program Files\Thorlabs\Kinesis",
        r"C:\Program Files (x86)\Thorlabs\Kinesis",
    ]
    # В PyInstaller --onedir DLL лежат в _internal/ рядом с exe
    if getattr(sys, 'frozen', False):
        internal = os.path.join(os.path.dirname(sys.executable), '_internal')
        if os.path.isdir(internal):
            paths.append(internal)
    return paths


def _add_kinesis_to_path():
    """Добавляет пути к Kinesis DLL в поиск загрузчика и сбрасывает кеш."""
    for p in _kinesis_paths():
        if os.path.isdir(p):
            try:
                os.add_dll_directory(p)
                logger.info(f"[Thorlabs] Добавлен путь к DLL: {p}")
            except AttributeError:
                logger.warning("[Thorlabs] os.add_dll_directory не поддерживается")

    # Сбрасываем кеш модулей thorlabs_kinesis — чтобы перезагрузить их с DLL
    for mod in list(sys.modules.keys()):
        if 'thorlabs_kinesis' in mod and mod != __name__:
            del sys.modules[mod]

KDC_ENCODER_STEP = 0.03
BSM_ENCODER_STEP = 0.002


def _scan_via(driver_module, label):
    """Пытается получить список серийников через один DLL-модуль."""
    from ctypes import create_string_buffer

    dll_avail = getattr(driver_module, 'DLL_AVAILABLE', False)
    logger.info(f"[Thorlabs.{label}] DLL_AVAILABLE={dll_avail}")

    if not dll_avail:
        logger.warning(f"[Thorlabs.{label}] DLL недоступна — пропускаем")
        return []

    driver_module.TLI_BuildDeviceList()
    time.sleep(0.5)

    device_count = driver_module.TLI_GetDeviceListSize()
    logger.info(f"[Thorlabs.{label}] Найдено устройств: {device_count}")

    if device_count and device_count > 0:
        buf = create_string_buffer(1024)
        driver_module.TLI_GetDeviceListExt(buf, 1024)
        raw = buf.value.decode('utf-8')
        serials = [s.strip() for s in raw.split(',') if s.strip()]
        logger.info(f"[Thorlabs.{label}] Серийные номера: {serials}")
        return serials
    return []


def get_thorlabs_serials():
    """Сканирует доступные устройства Thorlabs"""
    serials = []

    _add_kinesis_to_path()
    
    try:
        from Hardware.Stages.thorlabs_kinesis import benchtop_stepper_motor as bsm
        from Hardware.Stages.thorlabs_kinesis import KCube_DC_Servo as kdc
    except Exception as e:
        logger.warning(f"[Thorlabs] DLL не найдена: {e}")
        return serials

    logger.info(">>> Сканирование Thorlabs через KDC...")
    serials.extend(_scan_via(kdc, 'KDC'))

    logger.info(">>> Сканирование Thorlabs через BSM...")
    serials.extend(_scan_via(bsm, 'BSM'))

    # Убираем дубликаты
    serials = list(dict.fromkeys(serials))
    return serials


class ThorlabsAxis:
    def __init__(self, serial_no, axis_type='KDC'):
        _add_kinesis_to_path()

        try:
            from Hardware.Stages.thorlabs_kinesis import benchtop_stepper_motor as bsm
            from Hardware.Stages.thorlabs_kinesis import KCube_DC_Servo as kdc
        except FileNotFoundError as e:
            raise RuntimeError(f"Thorlabs DLL не найдена: {e}")
        
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