"""
Fix PowerParams via C API — focused script.
Try SetPowerParams + PersistSettings with various strategies.
"""

import sys, os, time
from ctypes import c_short, c_int, c_long, c_char_p, c_uint, c_ushort as c_word, byref

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, ".."))

from Hardware.Stages.thorlabs_kinesis import benchtop_stepper_motor as bsm

SERIAL = "70864299"
ENCODER_STEP = 0.002

def s(x): return x.value if hasattr(x, 'value') else int(x)
def ser(): return c_char_p(SERIAL.encode("utf-8"))


def open_device():
    bsm.TLI_BuildDeviceList()
    for i in range(3):
        if bsm.SBC_Open(ser()) == 0:
            time.sleep(0.5)
            return True
        time.sleep(1.0 * (i + 1))
    return False


def close_device():
    bsm.SBC_StopImmediate(ser(), c_short(1))
    time.sleep(0.1)
    bsm.SBC_StopImmediate(ser(), c_short(2))
    time.sleep(0.1)
    bsm.SBC_Close(ser())
    time.sleep(1.0)


def read_power(ch):
    bsm.SBC_RequestPowerParams(ser(), ch)
    time.sleep(0.1)
    pp = bsm.MOT_PowerParameters()
    bsm.SBC_GetPowerParams(ser(), ch, byref(pp))
    return s(pp.restPercentage), s(pp.movePercentage)


def write_power(ch, rest, move):
    pp = bsm.MOT_PowerParameters()
    pp.restPercentage = c_word(rest)
    pp.movePercentage = c_word(move)
    err = bsm.SBC_SetPowerParams(ser(), ch, byref(pp))
    time.sleep(0.3)
    return err


def persist(ch):
    result = bsm.SBC_PersistSettings(ser(), ch)
    time.sleep(1.0)
    return result


def main():
    print("=== FIX POWER PARAMS ===")

    if not bsm or not bsm.DLL_AVAILABLE:
        print("BSM DLL not available!")
        return 1

    if not open_device():
        print("Cannot open device!")
        return 1

    print("Device opened")

    for ch in [c_short(1), c_short(2)]:
        ch_num = s(ch)
        print(f"\n=== CHANNEL {ch_num} ===")

        # Read current
        rest, move = read_power(ch)
        print(f"  CURRENT: rest={rest}% move={move}%")

        # Strategy 1: Set 6%/6% and persist
        print(f"  Setting 6%/6%...")
        err = write_power(ch, 6, 6)
        print(f"  SetPowerParams err={err}")
        
        # Read back immediately
        rest2, move2 = read_power(ch)
        print(f"  READBACK (no persist): rest={rest2}% move={move2}%")
        
        # Persist
        persist_ok = persist(ch)
        print(f"  PersistSettings: {persist_ok}")
        
        # Read back after persist
        rest3, move3 = read_power(ch)
        print(f"  READBACK (after persist): rest={rest3}% move={move3}%")

        # Strategy 2: Try different values to find one that sticks
        if rest3 != 6 or move3 != 6:
            print(f"\n  6% didn't stick, trying sweep...")
            for target in [0, 3, 5, 8, 10, 15, 20]:
                write_power(ch, target, target)
                persist(ch)
                time.sleep(0.5)
                r, m = read_power(ch)
                print(f"    target={target}% -> actual rest={r}% move={m}% {'MATCH' if r == target else 'MISMATCH'}")
                if r == target:
                    print(f"    >>> FOUND MATCHING VALUE: {target}%")
                    break

    close_device()
    print("\n=== DONE ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
