# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 14:42:03 2026
@author: Александр
"""
# Hardware/Stages/LBTEK/lbtek_stages.py
import time
import logging
import ctypes
from ctypes import c_int, c_float
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Загрузка DLL ---
try:
    dll_path = Path(__file__).parent.resolve() / "LBTEKx64" / "MoverLibrary.dll"
    dll = ctypes.CDLL(str(dll_path))
except Exception as e:
    raise ImportError(f"Критическая ошибка: Не удалось загрузить MoverLibrary.dll: {e}")

# --- Настройка типов ---
dll.GetCurrentPos.restype = c_float
dll.GetCurrentPos.argtypes = [c_int, c_int]

dll.openEmcvx.restype = c_int
dll.openEmcvx.argtypes = [ctypes.c_char_p]

dll.closeEmcvx.restype = c_int
dll.closeEmcvx.argtypes = [c_int]

dll.isOpen.restype = c_int
dll.isOpen.argtypes = [ctypes.c_char_p]

dll.initAxis.restype = c_int
dll.initAxis.argtypes = [c_int, c_int, ctypes.c_char_p, c_int]

dll.setJogTime.restype = c_int
dll.setJogTime.argtypes = [c_int, c_int, c_int]

dll.setJogStep.restype = c_int
dll.setJogStep.argtypes = [c_int, c_int, c_float]

dll.getJogStep.restype = c_float
dll.getJogStep.argtypes = [c_int, c_int]

dll.moveEmcvx.restype = c_int
dll.moveEmcvx.argtypes = [c_int, c_int, c_int]

dll.getDoingState.restype = c_int
dll.getDoingState.argtypes = [c_int, c_int]

dll.getErrorCode.restype = c_int
dll.getErrorCode.argtypes = [c_int, c_int]


class LimitPositionException(Exception):
    pass


class _LBTEK_Internal:
    min_position = -15000
    max_position = 15000

    def __init__(self, serial_no):
        if not serial_no:
            raise ValueError("Не указан COM-порт для LBTEK.")

        self.serial_no_bytes = serial_no.encode('utf-8')
        self.handle = dll.openEmcvx(self.serial_no_bytes)
        logger.info(f"[LBTEK.__init__] handle={self.handle}, port={serial_no}")

        if not (self.handle > 0 and dll.isOpen(self.serial_no_bytes)):
            if self.handle > 0:
                dll.closeEmcvx(self.handle)
            raise ConnectionError(f"Не удалось открыть LBTEK на порту '{serial_no}'.")

        try:
            result = dll.initAxis(self.handle, 1, b"EM-LSS65-30C1", 1)
            logger.info(f"[LBTEK.__init__] initAxis result={result}")
            
            if result != 0:
                error_code = dll.getErrorCode(self.handle, 1)
                logger.error(f"[LBTEK.__init__] getErrorCode={error_code}")
                raise RuntimeError(f"initAxis вернула код ошибки {result} (errorCode={error_code}). "
                                   f"Возможно, это не LBTEK контроллер.")
        except Exception as e:
            self.close()
            raise RuntimeError(f"Ошибка инициализации оси LBTEK на '{serial_no}': {e}")

    def get_position(self):
        pos_mm = dll.GetCurrentPos(self.handle, 1)
        pos_mkm = pos_mm * 1000.0
        logger.info(f"[LBTEK.get_position] pos_mm={pos_mm}, pos_mkm={pos_mkm}")
        return pos_mkm

    def jog_by(self, step_mkm):
        current_pos = self.get_position()
        target = current_pos + step_mkm
        logger.info(f"[LBTEK.jog_by] current={current_pos}, step={step_mkm}, target={target}")

        if not (self.min_position < target < self.max_position):
            raise LimitPositionException('Превышен предел хода для LBTEK.')

        step_mm = step_mkm / 1000.0
        dll.setJogStep(self.handle, 1, abs(step_mm))
        direction = 0x07 if step_mm > 0 else 0x08
        logger.info(f"[LBTEK.jog_by] direction={hex(direction)}, step_mm={abs(step_mm)}")
        dll.moveEmcvx(self.handle, 1, direction)
        self.wait_until_idle()
        logger.info(f"[LBTEK.jog_by] завершено")

    def move_home(self):
        logger.info(f"[LBTEK.move_home] Отправляю команду home")
        dll.moveEmcvx(self.handle, 1, 0x02)
        self.wait_until_idle()

    def wait_until_idle(self, timeout=15.0):
        start_time = time.time()
        while time.time() - start_time < timeout:
            state = dll.getDoingState(self.handle, 1)
            if state == 0:
                logger.info(f"[LBTEK.wait_until_idle] Остановка за {time.time()-start_time:.2f}с")
                return
            time.sleep(0.05)
        raise TimeoutError("Ожидание остановки LBTEK превысило таймаут.")

    def close(self):
        if hasattr(self, 'handle') and self.handle > 0:
            dll.closeEmcvx(self.handle)
            self.handle = 0
            logger.info(f"[LBTEK.close] Закрыто")

    def __del__(self):
        self.close()


class LBTEKAxis:
    def __init__(self, identifier):
        self.stage = _LBTEK_Internal(serial_no=identifier)

    def get_position(self):
        return self.stage.get_position()

    def move_relative(self, distance_mkm):
        self.stage.jog_by(distance_mkm)

    def move_home(self):
        self.stage.move_home()

    def wait_for_stop(self):
        pass

    def close(self):
        self.stage.close()