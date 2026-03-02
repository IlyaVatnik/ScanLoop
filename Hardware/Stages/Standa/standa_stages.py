# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 16:48:51 2026

@author: Александр
"""
__data__='2026.03.02'
__version__='2.4'

# standa_stages.py

import sys
import os

# Инициализация и импорт библиотеки pyximc (по аналогии с вашим кодом)
if sys.version_info >= (3, 0):
    import urllib.parse
if __name__ == "__main__":
    from pyximc import *
else:
    try:
        from .pyximc import *
    except ImportError as err:
        print("Can't import pyximc module. Check if pyximc.py is in the directory.")
        exit()
    except OSError as err:
        print("Can't load libximc library. Check shared libraries.")
        exit()

class StandaEnvironment:
    """
    Синглтон-помощник для однократного поиска всех устройств Standa.
    Это предотвращает долгий поиск (enumerate) при инициализации каждой отдельной оси.
    """
    _devices_map = {}
    _is_initialized = False

    @classmethod
    def initialize(cls):
        if cls._is_initialized:
            return

        sbuf = create_string_buffer(64)
        lib.ximc_version(sbuf)
        print("libximc version: " + sbuf.raw.decode())

        devenum = lib.enumerate_devices(EnumerateFlags.ENUMERATE_PROBE, None)
        dev_count = lib.get_device_count(devenum)
        
        controller_name = controller_name_t()
        for dev_ind in range(dev_count):
            enum_name = lib.get_device_name(devenum, dev_ind)
            result = lib.get_enumerate_device_controller_name(devenum, dev_ind, byref(controller_name))
            if result == Result.Ok:
                friendly_name = str(controller_name.ControllerName.decode('utf-8'))
                port = enum_name.decode('utf-8')
                # Сохраняем как {'Axis 1': 'xi-com:\\.\COM3'}
                cls._devices_map[friendly_name] = port
        
        cls._is_initialized = True

    @classmethod
    def get_port_by_name(cls, friendly_name):
        cls.initialize()
        for name, port in cls._devices_map.items():
            if friendly_name in name:
                return port.encode('utf-8')
        raise ValueError(f"Device with name containing '{friendly_name}' not found!")


class StandaAxis:
    """
    Класс-обертка для управления одной осью (одним мотором) Standa.
    """
    def __init__(self, identifier):
        """identifier - это имя контроллера, например 'Axis 1'"""
        port_name = StandaEnvironment.get_port_by_name(identifier)
        self.device_id = lib.open_device(port_name)
        if self.device_id <= 0:
            raise RuntimeError(f"Failed to open device {identifier} on port {port_name}")

    def get_position(self):
        x_pos = get_position_t()
        lib.get_position(self.device_id, byref(x_pos))
        # Масштабный коэффициент перевода шагов в микрометры
        return round(x_pos.Position * 2.5, 1)

    def move_relative(self, distance_mkm):
        steps = int(distance_mkm / 2.5)
        lib.command_movr(self.device_id, steps, 0)

    def move_home(self):
        lib.command_home(self.device_id)

    def wait_for_stop(self):
        # 11 - интервал опроса остановки (ms)
        lib.command_wait_for_stop(self.device_id, 11)

    def close(self):
        lib.close_device(byref(cast(self.device_id, POINTER(c_int))))