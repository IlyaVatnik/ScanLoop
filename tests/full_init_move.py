"""Full parameter setup + move test with correct values from XML defaults."""
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
    0x00000001: "FWD_LIMIT", 0x00000002: "REV_LIMIT",
    0x00000004: "FWD_MOVE", 0x00000008: "REV_MOVE",
    0x00000010: "FWD_SWLIM", 0x00000020: "REV_SWLIM",
    0x00000040: "MOTOR_CONN", 0x00000080: "HOMING",
    0x00000100: "HOMED", 0x00000200: "MOVING",
    0x00000400: "ENABLED", 0x00000800: "DISABLED",
    0x00001000: "ERROR", 0x00002000: "STALL",
}

def show_ch(ch):
    b = bsm.SBC_GetStatusBits(SER, c_short(ch))
    p = bsm.SBC_GetPosition(SER, c_short(ch))
    flags = [n for m, n in STATUS.items() if b & m]
    return "ch%d pos=%d status=0x%08X %s" % (ch, p, b, " | ".join(flags))

# NRT100/M: 200 steps/rev, gear=1, pitch=1mm => 200 steps/mm
STEPS_PER_MM = 200
# So vel 30mm/s = 6000 steps/s, acc 30mm/s^2 = 6000 steps/s^2
VEL = 6000
ACC = 6000
HOME_VEL = 200  # 1mm/s

print("=== INIT both channels ===")
for ch in [1, 2]:
    ch_s = c_short(ch)
    bsm.SBC_StopImmediate(SER, ch_s)
    bsm.SBC_ClearMessageQueue(SER, ch_s)
    time.sleep(0.3)

    # Power: 100%/100%
    pp = bsm.MOT_PowerParameters()
    pp.restPercentage = c_word(100)
    pp.movePercentage = c_word(100)
    bsm.SBC_SetPowerParams(SER, ch_s, pp)

    # Velocity/acceleration from XML defaults
    bsm.SBC_SetVelParams(SER, ch_s, c_int(VEL), c_int(ACC))

    # Homing velocity
    bsm.SBC_SetHomingVelocity(SER, ch_s, c_uint(HOME_VEL))

    # Backlash
    bsm.SBC_SetBacklash(SER, ch_s, c_long(0))

    # Travel mode: linear
    bsm.SBC_SetMotorTravelMode(SER, ch_s, c_int(1))  # MOT_Linear

    # Set axis limits (in steps): 0 to 20000 (0-100mm)
    bsm.SBC_SetStageAxisLimits(SER, ch_s, c_int(0), c_int(20000))

    # Position counter = 0
    bsm.SBC_StopImmediate(SER, ch_s)
    time.sleep(0.2)
    bsm.SBC_SetPositionCounter(SER, ch_s, c_long(0))

    # Read back and verify
    vel_r = c_int(); acc_r = c_int()
    bsm.SBC_GetVelParams(SER, ch_s, vel_r, acc_r)
    pp_r = bsm.MOT_PowerParameters()
    bsm.SBC_GetPowerParams(SER, ch_s, pp_r)
    print("  %s vel=%d acc=%d power=%d/%d" % (
        show_ch(ch), vel_r.value, acc_r.value,
        pp_r.restPercentage, pp_r.movePercentage))

time.sleep(0.5)

print("")
print("=== READ AXIS LIMITS ===")
for ch in [1, 2]:
    mn = bsm.SBC_GetStageAxisMinPos(SER, c_short(ch))
    mx = bsm.SBC_GetStageAxisMaxPos(SER, c_short(ch))
    mode = bsm.SBC_GetMotorTravelMode(SER, c_short(ch))
    print("  ch%d: min=%d max=%d travelMode=%d" % (ch, mn, mx, mode))

print("")
print("=== WHEN READY: will move ch1 +500 steps (2.5mm) ===")
print("=== WATCH THE STAGE NOW ===")
time.sleep(3)

print("--- MOVE ch1 +500 ---")
bsm.SBC_StartPolling(SER, c_short(1), c_int(100))
time.sleep(0.1)
bsm.SBC_SetMoveRelativeDistance(SER, c_short(1), c_int(500))
err = bsm.SBC_MoveRelativeDistance(SER, c_short(1))
print("  err=%d" % err)
time.sleep(4)
print("  %s" % show_ch(1))
bsm.SBC_StopPolling(SER, c_short(1))

time.sleep(2)

print("--- MOVE ch1 -500 (back) ---")
bsm.SBC_StartPolling(SER, c_short(1), c_int(100))
time.sleep(0.1)
bsm.SBC_SetMoveRelativeDistance(SER, c_short(1), c_int(-500))
err = bsm.SBC_MoveRelativeDistance(SER, c_short(1))
print("  err=%d" % err)
time.sleep(4)
print("  %s" % show_ch(1))
bsm.SBC_StopPolling(SER, c_short(1))

time.sleep(2)

print("")
print("=== MOVE ch2 +500 steps ===")
print("=== WATCH THE STAGE NOW ===")
time.sleep(3)

bsm.SBC_StartPolling(SER, c_short(2), c_int(100))
time.sleep(0.1)
bsm.SBC_SetMoveRelativeDistance(SER, c_short(2), c_int(500))
err = bsm.SBC_MoveRelativeDistance(SER, c_short(2))
print("  err=%d" % err)
time.sleep(4)
print("  %s" % show_ch(2))
bsm.SBC_StopPolling(SER, c_short(2))

time.sleep(2)

print("--- MOVE ch2 -500 (back) ---")
bsm.SBC_StartPolling(SER, c_short(2), c_int(100))
time.sleep(0.1)
bsm.SBC_SetMoveRelativeDistance(SER, c_short(2), c_int(-500))
err = bsm.SBC_MoveRelativeDistance(SER, c_short(2))
print("  err=%d" % err)
time.sleep(4)
print("  %s" % show_ch(2))
bsm.SBC_StopPolling(SER, c_short(2))

print("")
print("=== DONE ===")
print("  %s" % show_ch(1))
print("  %s" % show_ch(2))
