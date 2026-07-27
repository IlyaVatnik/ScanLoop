"""Disable soft limits with correct type and test movement."""
import os, sys, time
os.add_dll_directory(r"C:\Program Files\Thorlabs\Kinesis")
sys.path.insert(0, r"C:\Users\Adm\Desktop\ScanLoop")

import clr
clr.AddReference(r"C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.DeviceManagerCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
DeviceManagerCLI.BuildDeviceList()

import Hardware.Stages.thorlabs_kinesis.benchtop_stepper_motor as bsm
from ctypes import c_short, c_int, c_int16, c_uint, c_long
from ctypes import c_ushort as c_word

SER = b"70864299"
bsm.TLI_BuildDeviceList()
bsm.SBC_Open(SER)

STATUS = {
    0x00000001: "FWD_LIM", 0x00000002: "REV_LIM",
    0x00000010: "FWD_SWLIM", 0x00000020: "REV_SWLIM",
    0x00000080: "HOMING", 0x00000100: "HOMED",
    0x00000200: "MOVING", 0x00000400: "ENABLED",
    0x00001000: "ERROR", 0x00002000: "STALL",
}
def show(ch):
    b = bsm.SBC_GetStatusBits(SER, c_short(ch))
    p = bsm.SBC_GetPosition(SER, c_short(ch))
    flags = " | ".join(n for m, n in STATUS.items() if b & m) or "OK"
    return "ch%d: pos=%-6d %s" % (ch, p, flags)

def wait_done(ch, timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(0.2)
        b = bsm.SBC_GetStatusBits(SER, c_short(ch))
        if not (b & 0x00000200):
            return

def move(ch, steps):
    bsm.SBC_StartPolling(SER, c_short(ch), c_int(100))
    time.sleep(0.1)
    bsm.SBC_SetMoveRelativeDistance(SER, c_short(ch), c_int(steps))
    bsm.SBC_MoveRelativeDistance(SER, c_short(ch))
    wait_done(ch)
    bsm.SBC_StopPolling(SER, c_short(ch))

# === FIX SOFT LIMITS ===
print("=== BEFORE: SoftLimitMode ===")
for ch in [1, 2]:
    mode = bsm.SBC_GetSoftLimitMode(SER, c_short(ch))
    print("  ch%d: %d" % (ch, mode))

print("=== SET AllowAllMoves ===")
for ch in [1, 2]:
    bsm.SBC_SetLimitsSoftwareApproachPolicy(SER, c_short(ch), c_int16(2))
    time.sleep(0.1)
    mode = bsm.SBC_GetSoftLimitMode(SER, c_short(ch))
    print("  ch%d: %d" % (ch, mode))

print("=== SET AXIS LIMITS 0..100000 ===")
for ch in [1, 2]:
    bsm.SBC_SetStageAxisLimits(SER, c_short(ch), c_int(0), c_int(100000))
    time.sleep(0.1)
    mn = bsm.SBC_GetStageAxisMinPos(SER, c_short(ch))
    mx = bsm.SBC_GetStageAxisMaxPos(SER, c_short(ch))
    print("  ch%d: min=%d max=%d" % (ch, mn, mx))

# Init both
for ch in [1, 2]:
    bsm.SBC_StopImmediate(SER, c_short(ch))
    bsm.SBC_ClearMessageQueue(SER, c_short(ch))
    time.sleep(0.3)
    pp = bsm.MOT_PowerParameters()
    pp.restPercentage = c_word(100)
    pp.movePercentage = c_word(100)
    bsm.SBC_SetPowerParams(SER, c_short(ch), pp)
    bsm.SBC_SetVelParams(SER, c_short(ch), c_int(6000), c_int(6000))
    bsm.SBC_StopImmediate(SER, c_short(ch))
    time.sleep(0.2)
    bsm.SBC_SetPositionCounter(SER, c_short(ch), c_long(0))

print()
print("STATUS:")
print("  %s" % show(1))
print("  %s" % show(2))
print()
print("MOVING IN 3 SECONDS...")
time.sleep(3)

print(">>> CH1 +500 steps <<<")
move(1, 500)
print("  %s" % show(1))
time.sleep(2)

print(">>> CH1 -500 steps <<<")
move(1, -500)
print("  %s" % show(1))
time.sleep(2)

print(">>> CH2 +500 steps <<<")
move(2, 500)
print("  %s" % show(2))
time.sleep(2)

print(">>> CH2 -500 steps <<<")
move(2, -500)
print("  %s" % show(2))

print()
print("FINAL:")
print("  %s" % show(1))
print("  %s" % show(2))
