"""Full C API test: PowerParams + motor movement."""
import os, sys, time
os.add_dll_directory(r"C:\Program Files\Thorlabs\Kinesis")
sys.path.insert(0, r"C:\Users\Adm\Desktop\ScanLoop")

import clr
clr.AddReference(r"C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.DeviceManagerCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
DeviceManagerCLI.BuildDeviceList()

import Hardware.Stages.thorlabs_kinesis.benchtop_stepper_motor as bsm
from ctypes import c_short, c_int, c_long, c_uint, c_ulong, c_char, POINTER

serial = b"70864299"

err = bsm.TLI_BuildDeviceList()
print(f"TLI_BuildDeviceList: {err}")

bsm.lib.TLI_GetDeviceListSize.restype = c_ulong
size = bsm.lib.TLI_GetDeviceListSize()
print(f"DeviceListSize: {size}")

err = bsm.SBC_Open(serial)
print(f"SBC_Open: {err}")

if err != 0:
    print("Cannot open device!")
    sys.exit(1)

# --- Hardware info ---
n = bsm.SBC_GetNumChannels(serial)
print(f"NumChannels: {n}")

# --- Power params for all channels ---
print("\n=== Power Parameters ===")
for ch in range(n):
    pp = bsm.MOT_PowerParameters()
    err = bsm.SBC_GetPowerParams(serial, c_short(ch), pp)
    print(f"  ch{ch}: restPercentage={pp.restPercentage}, movePercentage={pp.movePercentage}")

# --- Vel params ---
print("\n=== Velocity Parameters ===")
for ch in range(n):
    vel = c_int()
    acc = c_int()
    bsm.SBC_GetVelParams(serial, c_short(ch), vel, acc)
    print(f"  ch{ch}: vel={vel.value}, acc={acc.value}")

# --- Positions ---
print("\n=== Positions ===")
for ch in range(n):
    pos = bsm.SBC_GetPosition(serial, c_short(ch))
    print(f"  ch{ch}: position={pos}")

# --- Status bits ---
print("\n=== Status Bits ===")
for ch in range(n):
    bits = bsm.SBC_GetStatusBits(serial, c_short(ch))
    print(f"  ch{ch}: status=0x{bits:08X}")

# --- Input voltage ---
print("\n=== Input Voltage ===")
for ch in range(n):
    v = bsm.SBC_GetInputVoltage(serial, c_short(ch))
    print(f"  ch{ch}: voltage={v}")

# --- Try to set PowerParams to 6%/6% ---
print("\n=== Setting PowerParams to 6%/6% ===")
for ch in range(n):
    pp = bsm.MOT_PowerParameters()
    pp.restPercentage = 6
    pp.movePercentage = 6
    err = bsm.SBC_SetPowerParams(serial, c_short(ch), pp)
    print(f"  ch{ch}: SetPowerParams returned {err}")

# --- Verify ---
print("\n=== Verify PowerParams ===")
for ch in range(n):
    pp = bsm.MOT_PowerParameters()
    bsm.SBC_GetPowerParams(serial, c_short(ch), pp)
    print(f"  ch{ch}: rest={pp.restPercentage}, move={pp.movePercentage}")
