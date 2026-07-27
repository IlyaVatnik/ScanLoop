import os, sys, time
os.add_dll_directory(r"C:\Program Files\Thorlabs\Kinesis")
sys.path.insert(0, r"C:\Users\Adm\Desktop\ScanLoop")

import clr
clr.AddReference(r"C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.DeviceManagerCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
DeviceManagerCLI.BuildDeviceList()

import Hardware.Stages.thorlabs_kinesis.benchtop_stepper_motor as bsm
from ctypes import c_short, c_int, c_uint, c_long, byref
from ctypes import c_ushort as c_word

SER = b"70864299"
bsm.TLI_BuildDeviceList()
bsm.SBC_Open(SER)

for ch in [1, 2]:
    bsm.SBC_StopImmediate(SER, c_short(ch))
    time.sleep(0.2)
    pp = bsm.MOT_PowerParameters()
    pp.restPercentage = c_word(100)
    pp.movePercentage = c_word(100)
    bsm.SBC_SetPowerParams(SER, c_short(ch), pp)
    bsm.SBC_SetVelParams(SER, c_short(ch), c_int(15000), c_int(15000))
    bsm.SBC_SetPositionCounter(SER, c_short(ch), c_long(0))

time.sleep(0.5)

def do_move(ch, steps, label):
    bsm.SBC_StartPolling(SER, c_short(ch), c_int(100))
    time.sleep(0.1)
    bsm.SBC_SetMoveRelativeDistance(SER, c_short(ch), c_int(steps))
    err = bsm.SBC_MoveRelativeDistance(SER, c_short(ch))
    wait = abs(steps) / 5000.0 + 1.5
    time.sleep(wait)
    p = bsm.SBC_GetPosition(SER, c_short(ch))
    bsm.SBC_StopPolling(SER, c_short(ch))
    print("  ch%d %s: %6d steps -> pos=%6d" % (ch, label, steps, p))
    return p

print("Both stages at 0")
print("")

print("--- CH1: forward 3000 steps (~6mm) ---")
do_move(1, 3000, "FWD")
time.sleep(2)

print("--- CH1: back 3000 steps ---")
do_move(1, -3000, "BWD")
time.sleep(2)

print("")
print("--- CH2: forward 3000 steps (~6mm) ---")
do_move(2, 3000, "FWD")
time.sleep(2)

print("--- CH2: back 3000 steps ---")
do_move(2, -3000, "BWD")
time.sleep(2)

print("")
print("--- CH1: forward 10000 steps (~20mm) ---")
do_move(1, 10000, "BIG")
time.sleep(2)

print("--- CH1: back 10000 steps ---")
do_move(1, -10000, "BIG")
time.sleep(2)

print("")
print("--- CH2: forward 10000 steps (~20mm) ---")
do_move(2, 10000, "BIG")
time.sleep(2)

print("--- CH2: back 10000 steps ---")
do_move(2, -10000, "BIG")

print("")
print("Done.")
