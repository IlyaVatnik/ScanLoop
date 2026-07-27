"""Step-by-step move with init first, then wait for user confirmation."""
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

STATUS = {
    0x00000001: "FWD_LIM", 0x00000002: "REV_LIM",
    0x00000010: "FWD_SWLIM", 0x00000020: "REV_SWLIM",
    0x00000040: "CONN", 0x00000080: "HOMING",
    0x00000100: "HOMED", 0x00000200: "MOVING",
    0x00000400: "ENABLED", 0x00001000: "ERROR",
    0x00002000: "STALL",
}

def show(ch):
    b = bsm.SBC_GetStatusBits(SER, c_short(ch))
    p = bsm.SBC_GetPosition(SER, c_short(ch))
    flags = " | ".join(n for m, n in STATUS.items() if b & m) or "OK"
    print("  ch%d: pos=%-6d %s" % (ch, p, flags))

def do_move(ch, steps):
    bsm.SBC_StartPolling(SER, c_short(ch), c_int(100))
    time.sleep(0.1)
    bsm.SBC_SetMoveRelativeDistance(SER, c_short(ch), c_int(steps))
    err = bsm.SBC_MoveRelativeDistance(SER, c_short(ch))
    t0 = time.time()
    while time.time() - t0 < abs(steps) / 3000.0 + 5:
        time.sleep(0.2)
        b = bsm.SBC_GetStatusBits(SER, c_short(ch))
        if not (b & 0x00000200):
            break
    p = bsm.SBC_GetPosition(SER, c_short(ch))
    bsm.SBC_StopPolling(SER, c_short(ch))
    return p

# === PHASE 1: INIT (no movement) ===
print("=== INIT ===")
for ch in [1, 2]:
    ch_s = c_short(ch)
    bsm.SBC_StopImmediate(SER, ch_s)
    bsm.SBC_ClearMessageQueue(SER, ch_s)
    time.sleep(0.3)
    pp = bsm.MOT_PowerParameters()
    pp.restPercentage = c_word(100)
    pp.movePercentage = c_word(100)
    bsm.SBC_SetPowerParams(SER, ch_s, pp)
    bsm.SBC_SetVelParams(SER, ch_s, c_int(6000), c_int(6000))
    bsm.SBC_SetBacklash(SER, ch_s, c_long(0))
    bsm.SBC_StopImmediate(SER, ch_s)
    time.sleep(0.2)
    bsm.SBC_SetPositionCounter(SER, ch_s, c_long(0))

print("Ready.")
print("")
print("STEP 1: ch1 forward 500 steps")
p = do_move(1, 500)
show(1)
time.sleep(1)

print("")
print("STEP 2: ch1 back 500 steps")
p = do_move(1, -500)
show(1)
time.sleep(1)

print("")
print("STEP 3: ch2 forward 500 steps")
p = do_move(2, 500)
show(2)
time.sleep(1)

print("")
print("STEP 4: ch2 back 500 steps")
p = do_move(2, -500)
show(2)
time.sleep(1)

print("")
print("=== FINAL ===")
show(1)
show(2)
