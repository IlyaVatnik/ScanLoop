# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 13:51:31 2026

@author: Александр
"""

# === diagnostic_stages.py ===
# Положи в папку Hardware/Stages/Standa/ и запусти

from pyximc import *
from ctypes import byref

devenum = lib.enumerate_devices(EnumerateFlags.ENUMERATE_PROBE, None)
dev_count = lib.get_device_count(devenum)

print(f"Найдено устройств Standa: {dev_count}")

controller_name = controller_name_t()
for i in range(dev_count):
    enum_name = lib.get_device_name(devenum, i)
    lib.get_enumerate_device_controller_name(devenum, i, byref(controller_name))
    name = controller_name.ControllerName.decode('utf-8')
    port = enum_name.decode('utf-8')
    print(f"  [{i}] Port: {port}  |  ControllerName: '{name}'")

lib.free_enumerate_devices(devenum)
input("Нажми Enter...")