"""Test motor movement on ch1 (the active channel)."""
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
bsm.TLI_BuildDeviceList()
err = bsm.SBC_Open(serial)
print(f"SBC_Open: {err}")
if err != 0:
    sys.exit(1)

n = bsm.SBC_GetNumChannels(serial)
print(f"NumChannels: {n}")

# --- Check which channels have motors ---
print("\n=== Channel Status ===")
for ch in range(n):
    bits = bsm.SBC_GetStatusBits(serial, c_short(ch))
    v = bsm.SBC_GetInputVoltage(serial, c_short(ch))
    pos = bsm.SBC_GetPosition(serial, c_short(ch))
    print(f"  ch{ch}: status=0x{bits:08X} voltage={v} position={pos}")

# --- Set reasonable velocity for ch1 ---
print("\n=== Setting Velocity for ch1 ===")
vel = c_int()
acc = c_int()
bsm.SBC_GetVelParams(serial, c_short(1), vel, acc)
print(f"  Before: vel={vel.value}, acc={acc.value}")

# Set vel=50mm/s (in device units), acc=100mm/s^2
# Need to figure out device units first
# NRT100 has 25nm resolution (roughly) - but let's try conservative values
# Typical: vel=30000 steps/s, acc=300000 steps/s^2
bsm.SBC_SetVelParams(serial, c_short(1), c_int(5000), c_int(10000))
bsm.SBC_GetVelParams(serial, c_short(1), vel, acc)
print(f"  After: vel={vel.value}, acc={acc.value}")

# --- Try to HOME ch1 ---
print("\n=== Homing ch1 ===")
print("  WARNING: Motor will move! Make sure it's safe!")
try:
    # First check what homing velocity we have
    hv = bsm.SBC_GetHomingVelocity(serial, c_short(1))
    print(f"  Homing velocity: {hv}")
    
    bsm.SBC_SetHomingVelocity(serial, c_short(1), c_uint(5000))
    hv2 = bsm.SBC_GetHomingVelocity(serial, c_short(1))
    print(f"  Set homing velocity to: {hv2}")
except Exception as e:
    print(f"  Homing velocity error: {e}")

# Actually send Home command
# Home() is not directly in the BSM DLL - let's check what movement functions exist
print("\n=== Movement Functions Available ===")
for attr in dir(bsm):
    if 'Move' in attr or 'Home' in attr or 'Home' in attr:
        print(f"  {attr}")

# Try MoveRelative (small move to test)
print("\n=== Testing small relative move on ch1 ===")
print("  Will move +100 steps...")
try:
    bsm.SBC_SetMoveRelativeDistance(serial, c_short(1), c_int(100))
    err = bsm.SBC_MoveRelativeDistance(serial, c_short(1))
    print(f"  MoveRelativeDistance returned: {err}")
    
    time.sleep(2)
    
    pos = bsm.SBC_GetPosition(serial, c_short(1))
    print(f"  Position after move: {pos}")
    
    bits = bsm.SBC_GetStatusBits(serial, c_short(1))
    print(f"  Status after move: 0x{bits:08X}")
except Exception as e:
    print(f"  Move error: {e}")
