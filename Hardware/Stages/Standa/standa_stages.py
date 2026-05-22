# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 16:48:51 2026
@author: Александр
"""
__data__='2026.04.27'
__version__='2.6.3'
# Hardware/Stages/Standa/standa_stages.py
import time
import logging
from ctypes import byref, c_int

from Hardware.Stages.Standa.pyximc import lib, get_position_t, status_t, Result

logger = logging.getLogger(__name__)


class StandaAxis:
    def __init__(self, identifier):
        self.device_id = -1

        port_name = b"xi-com:\\\\.\\" + identifier.encode('utf-8')
        self.device_id = lib.open_device(port_name)

        if self.device_id <= 0:
            raise RuntimeError(f"Не удалось подключиться к Standa на порту '{identifier}'.")

        x_pos = get_position_t()
        result = lib.get_position(self.device_id, byref(x_pos))
        if result != Result.Ok:
            self.close()
            raise RuntimeError(f"Контроллер '{identifier}' не отдает позицию.")

        # Проверяем статус при инициализации
        st = status_t()
        result_s = lib.get_status(self.device_id, byref(st))
        logger.info(f"[Standa.__init__] OK: device_id={self.device_id}, "
                    f"get_status result={result_s}, MvCmdSts={hex(st.MvCmdSts)}")

    def get_position(self):
        x_pos = get_position_t()
        lib.get_position(self.device_id, byref(x_pos))
        return x_pos.Position * 2.5

    def move_relative(self, distance_mkm):
        steps = int(distance_mkm / 2.5)
        logger.info(f"[Standa.move_relative] steps={steps}, device_id={self.device_id}")
        result = lib.command_movr(self.device_id, steps, 0)
        logger.info(f"[Standa.move_relative] command_movr result={result}")
        
        # Небольшая задержка перед polling
        time.sleep(0.05)
        
        self.wait_for_stop()
        logger.info(f"[Standa.move_relative] завершено")

    def move_home(self):
        lib.command_home(self.device_id)
        self.wait_for_stop()

    def wait_for_stop(self, timeout_s=10.0):
        """
        Polling статуса. MvCmdSts & 0x80 = команда выполняется.
        """
        logger.info(f"[Standa.wait_for_stop] Начало polling")
        start = time.time()
        st = status_t()

        while time.time() - start < timeout_s:
            result = lib.get_status(self.device_id, byref(st))
            if result != Result.Ok:
                logger.error(f"[Standa.wait_for_stop] get_status ошибка: {result}")
                break
            
            if time.time() - start < 0.1:
                logger.debug(f"[Standa.wait_for_stop] MvCmdSts={hex(st.MvCmdSts)}")
            
            if not (st.MvCmdSts & 0x80):
                logger.info(f"[Standa.wait_for_stop] Остановка за {time.time()-start:.2f}с")
                return
            time.sleep(0.05)

        logger.warning(f"[Standa.wait_for_stop] Таймаут {timeout_s}с")

    def close(self):
        if hasattr(self, 'device_id') and self.device_id > 0:
            device_id_c = c_int(self.device_id)
            lib.close_device(byref(device_id_c))
            self.device_id = 0

    def __del__(self):
        self.close()