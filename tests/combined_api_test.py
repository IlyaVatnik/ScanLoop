"""Test: init .NET DeviceManager first, then try C API."""
import os, sys, time, clr

KINESIS = r"C:\Program Files\Thorlabs\Kinesis"
os.add_dll_directory(KINESIS)
os.environ["PATH"] = KINESIS + ";" + os.environ.get("PATH", "")

clr.AddReference(os.path.join(KINESIS, "Thorlabs.MotionControl.DeviceManagerCLI.dll"))
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI

print("=== .NET DeviceManager init ===")
DeviceManagerCLI.BuildDeviceList()
print("BuildDeviceList done")

# Now check C API device list
sys.path.insert(0, r"C:\Users\Adm\Desktop\ScanLoop")
import Hardware.Stages.thorlabs_kinesis.benchtop_stepper_motor as bsm
print(f"\nDLL_AVAILABLE: {bsm.DLL_AVAILABLE}")

err = bsm.TLI_BuildDeviceList()
print(f"C API TLI_BuildDeviceList: {err}")

from ctypes import c_ulong
bsm.lib.TLI_GetDeviceListSize.restype = c_ulong
size = bsm.lib.TLI_GetDeviceListSize()
print(f"C API TLI_GetDeviceListSize: {size}")

from ctypes import c_char, c_short
serial = b'70864299'
err2 = bsm.SBC_Open(serial)
print(f"C API SBC_Open: {err2}")

if err2 == 0:
    n = bsm.SBC_GetNumChannels(serial)
    print(f"NumChannels: {n}")
    
    from ctypes import c_int
    vel, acc = c_int(), c_int()
    bsm.SBC_GetVelParams(serial, c_short(0), vel, acc)
    print(f"VelParams ch0: vel={vel.value}, acc={acc.value}")
    
    pos = bsm.SBC_GetPosition(serial, c_short(0))
    print(f"Position ch0: {pos}")
