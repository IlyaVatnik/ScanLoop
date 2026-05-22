# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 13:51:31 2026

@author: Александр
"""

# === diag_standa_v2.py ===
# Положить в Hardware/Stages/Standa/ и запустить:
#   cd Hardware/Stages/Standa
#   python diag_standa_v2.py

import os
import sys
import ctypes

print("=" * 60)
print("ДИАГНОСТИКА STANDA")
print("=" * 60)

# 1. Проверяем рабочую директорию
cwd = os.getcwd()
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Рабочая директория:  {cwd}")
print(f"Директория скрипта:  {script_dir}")

# Принудительно переходим в директорию скрипта
os.chdir(script_dir)
print(f"Переключились в:     {os.getcwd()}")

# 2. Проверяем наличие DLL
dlls = ['libximc.dll', 'bindy.dll', 'xiwrapper.dll', 'keyfile.bin']
print("\nПроверка файлов:")
for dll_name in dlls:
    path = os.path.join(script_dir, dll_name)
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    status = f"OK ({size} bytes)" if exists else "НЕ НАЙДЕН!"
    print(f"  {dll_name}: {status}")

# 3. Пробуем загрузить DLL напрямую
print("\nЗагрузка libximc.dll напрямую...")
try:
    dll_path = os.path.join(script_dir, "libximc.dll")
    lib_direct = ctypes.WinDLL(dll_path)
    print(f"  OK: {lib_direct}")
except Exception as e:
    print(f"  ОШИБКА: {e}")
    print("  → Возможно не установлен Visual C++ Redistributable")

# 4. Пробуем импортировать pyximc
print("\nИмпорт pyximc...")
try:
    sys.path.insert(0, script_dir)
    from pyximc import *
    print(f"  OK, lib = {lib}")
except Exception as e:
    print(f"  ОШИБКА: {e}")
    print("  → pyximc не может загрузить libximc")
    input("\nНажми Enter...")
    sys.exit(1)

# 5. Перечисляем устройства
print("\nПоиск устройств Standa...")
from ctypes import byref

# Пробуем с разными флагами
for flag_name, flag in [
    ("ENUMERATE_PROBE", EnumerateFlags.ENUMERATE_PROBE),
    ("ENUMERATE_PROBE | ENUMERATE_NETWORK", 
     EnumerateFlags.ENUMERATE_PROBE | EnumerateFlags.ENUMERATE_NETWORK),
]:
    print(f"\n  Флаги: {flag_name}")
    try:
        devenum = lib.enumerate_devices(flag, None)
        dev_count = lib.get_device_count(devenum)
        print(f"  Найдено устройств: {dev_count}")

        controller_name = controller_name_t()
        for i in range(dev_count):
            enum_name = lib.get_device_name(devenum, i)
            lib.get_enumerate_device_controller_name(
                devenum, i, byref(controller_name))
            name = controller_name.ControllerName.decode('utf-8')
            port = enum_name.decode('utf-8')
            print(f"    [{i}] Port: {port}")
            print(f"         Name: '{name}'")

        lib.free_enumerate_devices(devenum)

    except Exception as e:
        print(f"  ОШИБКА: {e}")

# 6. Проверяем USB-устройства через Windows
print("\n" + "=" * 60)
print("COM-порты в системе:")
try:
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    if ports:
        for p in ports:
            print(f"  {p.device}: {p.description} [VID:PID={p.vid}:{p.pid}]")
    else:
        print("  Нет COM-портов!")
except ImportError:
    print("  (pyserial не установлен, пропускаем)")

print("\n" + "=" * 60)
input("Нажми Enter для выхода...")