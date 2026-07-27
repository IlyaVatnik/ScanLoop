"""
Diagnostic BSM v13 — .NET API initialization + C API movement

Root cause: Motor params (StepsPerRev, GearboxRatio, Pitch) are (0,0,0)
in corrupted EEPROM. C API SBC_SetMotorParamsExt returns err=1 (rejected).
Kinesis GUI uses .NET LoadMotorConfiguration which calls
UpdateDeviceUnitSettings internally — writes correct params to firmware RAM.

Strategy:
  Phase A: .NET API init (LoadMotorConfiguration writes motor params)
  Phase B: .NET movement test
  Phase C: Disconnect .NET, open C API, test movement (params in firmware RAM)
  Phase D: Persist settings to EEPROM (optional)
  Phase E: Summary
"""

import sys, os, time, logging, traceback
from datetime import datetime
from ctypes import c_short, c_int, c_uint, c_long, c_char_p, c_int16, byref
from ctypes import c_ushort as c_word

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

LOG_DIR = os.path.join(SCRIPT_DIR, "Logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, f"diagnostic_v13_{datetime.now():%Y-%m-%d_%H-%M-%S}.log")

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(message)s", datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_path, encoding="utf-8")],
)
log = logging.getLogger("diag")

SERIAL = "70864299"
ENCODER_STEP = 0.002
summary = []

STATUS_BITS = {
    0x00000001: "FWD_HW_LIMIT", 0x00000002: "REV_HW_LIMIT",
    0x00000004: "INMOTION_FWD", 0x00000008: "INMOTION_REV",
    0x00000010: "FWD_SW_LIMIT", 0x00000020: "REV_SW_LIMIT",
    0x00000040: "MOTOR_CONNECTED", 0x00000080: "HOMING",
    0x00000100: "HOMED", 0x00000200: "MOVING",
    0x00000400: "ENABLED", 0x00000800: "DISABLED",
    0x00001000: "ERROR", 0x00002000: "STALL",
    0x00004000: "TEMP_FAULT", 0x00008000: "CURRENT_FOLD",
}


def s(x): return x.value if hasattr(x, 'value') else int(x)
def decode(bits): return " | ".join(n for m, n in STATUS_BITS.items() if bits & m) or "NONE"
def sec(t): log.info(f"\n{'='*60}\n  {t}\n{'='*60}")
def sub(t): log.info(f"\n--- {t} ---")
def ser(): return c_char_p(SERIAL.encode("utf-8"))


# ── C API helpers ──────────────────────────────────────────────
try:
    from Hardware.Stages.thorlabs_kinesis import benchtop_stepper_motor as bsm
except Exception:
    bsm = None


def c_open():
    if not bsm or not bsm.DLL_AVAILABLE:
        return False
    bsm.TLI_BuildDeviceList()
    for i in range(1, 4):
        if bsm.SBC_Open(ser()) == 0:
            time.sleep(0.3)
            return True
        log.warning(f"  SBC_Open attempt {i}/3")
        time.sleep(1.0 * i)
    log.error("  SBC_Open FAILED")
    return False


def c_close():
    if not bsm:
        return
    try:
        bsm.SBC_StopProfiled(ser(), c_short(1))
        time.sleep(0.1)
        bsm.SBC_StopProfiled(ser(), c_short(2))
        time.sleep(0.3)
        bsm.SBC_Close(ser())
        time.sleep(1.0)
    except Exception as e:
        log.warning(f"  close error: {e}")


def c_pos(ch):
    bsm.SBC_RequestPosition(ser(), ch); time.sleep(0.01)
    return s(bsm.SBC_GetPosition(ser(), ch))


def c_status(ch):
    bsm.SBC_RequestStatusBits(ser(), ch); time.sleep(0.02)
    return s(bsm.SBC_GetStatusBits(ser(), ch))


def c_dump(ch, label=""):
    b = c_status(ch); p = c_pos(ch)
    log.info(f"  [{label}] Status=0x{b:08X}={decode(b)} Pos={p}({p*ENCODER_STEP:.4f}mm)")
    return b


def c_poll(ch, timeout=30):
    t0 = time.time(); last = None; st = 0
    while time.time() - t0 < timeout:
        time.sleep(0.05); v = c_pos(ch)
        if v == last: st += 1
        else: st = 0; last = v
        if st >= 10: return v
    log.warning(f"  poll timeout {timeout}s last={last}")
    return last


def c_move(ch, um):
    steps = int((um / 1000.0) / ENCODER_STEP)
    log.info(f"  move {um}um = {steps} steps")
    bsm.SBC_StartPolling(ser(), ch, c_int(100))
    bsm.SBC_ClearMessageQueue(ser(), ch); time.sleep(0.1)
    bsm.SBC_SetMoveRelativeDistance(ser(), ch, c_int(steps))
    err = bsm.SBC_MoveRelativeDistance(ser(), ch)
    log.info(f"  MoveRelative err={err}")
    r = c_poll(ch); bsm.SBC_StopPolling(ser(), ch)
    return r, err


def c_roundtrip(dist_um, label=""):
    expected = int((dist_um / 1000.0) / ENCODER_STEP)
    ch = c_short(2)
    before = c_pos(ch)

    sub(f"C API: Move +{dist_um}um{label}")
    _, err1 = c_move(ch, dist_um)
    after_p = c_pos(ch)
    d1 = after_p - before
    ok1 = abs(d1 - expected) <= 5
    log.info(f"  +{dist_um}um: delta={d1} expected={expected} err={err1} -> {'PASS' if ok1 else 'FAIL'}")
    summary.append({"label": f"C+{dist_um}um{label}", "expected": expected, "got": d1, "pass": ok1})

    sub(f"C API: Move -{dist_um}um{label}")
    _, err2 = c_move(ch, -dist_um)
    after_m = c_pos(ch)
    d2 = after_m - after_p
    ok2 = abs(d2 - (-expected)) <= 5
    log.info(f"  -{dist_um}um: delta={d2} expected={-expected} err={err2} -> {'PASS' if ok2 else 'FAIL'}")
    summary.append({"label": f"C-{dist_um}um{label}", "expected": -expected, "got": d2, "pass": ok2})
    time.sleep(0.3)


# ── .NET API helpers ──────────────────────────────────────────
def dotnet_init():
    """Initialize .NET DeviceManager and return (device, ch1, ch2)."""
    import clr
    KINESIS = r"C:\Program Files\Thorlabs\Kinesis"
    os.add_dll_directory(KINESIS)

    clr.AddReference(os.path.join(KINESIS, "Thorlabs.MotionControl.DeviceManagerCLI.dll"))
    clr.AddReference(os.path.join(KINESIS, "Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll"))
    clr.AddReference(os.path.join(KINESIS, "Thorlabs.MotionControl.GenericMotorCLI.dll"))

    from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
    from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

    log.info("  DeviceManagerCLI.Initialize()...")
    DeviceManagerCLI.Initialize()
    time.sleep(2)

    log.info("  DeviceManagerCLI.BuildDeviceList()...")
    result = DeviceManagerCLI.BuildDeviceList()
    time.sleep(3)
    log.info(f"  BuildDeviceList result: {result}")

    log.info(f"  CreateBenchtopStepperMotor({SERIAL})...")
    device = BenchtopStepperMotor.CreateBenchtopStepperMotor(SERIAL)
    time.sleep(1)

    log.info(f"  device.Connect({SERIAL})...")
    device.Connect(SERIAL)
    time.sleep(5)

    log.info(f"  IsConnected={device.IsConnected}, IsSimulation={device.IsSimulation}")

    if not device.IsConnected:
        log.error("  .NET Connect FAILED")
        return None, None, None

    ch1 = device.GetChannel(1)
    ch2 = device.GetChannel(2)
    return device, ch1, ch2


def dotnet_dump_channel(ch, label=""):
    """Dump channel state via .NET API."""
    try:
        pos = ch.GetPosition()
        log.info(f"  [{label}] .NET Position={pos}")
    except Exception as e:
        log.info(f"  [{label}] .NET GetPosition error: {e}")

    try:
        enabled = ch.IsEnabled
        state = ch.State
        log.info(f"  [{label}] IsEnabled={enabled}, State={state}")
    except Exception as e:
        log.info(f"  [{label}] State error: {e}")


def dotnet_read_motor_params(ch, label=""):
    """Read motor params via .NET API."""
    try:
        settings = ch.MotorDeviceSettings
        log.info(f"  [{label}] MotorDeviceSettings: {settings}")
    except Exception as e:
        log.info(f"  [{label}] MotorDeviceSettings error: {e}")

    try:
        pp = ch.GetPowerParams()
        log.info(f"  [{label}] PowerParams: rest={pp.restPercentage}%, move={pp.movePercentage}%")
    except Exception as e:
        log.info(f"  [{label}] GetPowerParams error: {e}")


def dotnet_test_move(ch, steps, label=""):
    """Move channel via .NET API and return position change."""
    try:
        pos_before = ch.GetPosition()
        log.info(f"  [{label}] .NET MoveRelative({steps}), pos_before={pos_before}")
        ch.MoveRelative(steps)
        time.sleep(5)
        pos_after = ch.GetPosition()
        delta = pos_after - pos_before
        log.info(f"  [{label}] .NET pos_after={pos_after}, delta={delta}")
        return delta
    except Exception as e:
        log.info(f"  [{label}] .NET MoveRelative error: {e}")
        return None


# ── MAIN ───────────────────────────────────────────────────────
def main():
    try:
        sec(f"DIAGNOSTIC BSM v13 — .NET init + C API move — {datetime.now():%Y-%m-%d %H:%M:%S}")
        log.info(f"  Log: {log_path}")

        # ════════════════════════════════════════════════════════
        # PHASE A: .NET API — LoadMotorConfiguration
        # ════════════════════════════════════════════════════════
        sec("PHASE A: .NET API INITIALIZATION")

        try:
            device, ch1, ch2 = dotnet_init()
        except Exception as e:
            log.error(f"  .NET init FAILED: {e}\n{traceback.format_exc()}")
            device = None

        if device and device.IsConnected:
            sub("A1: Dump channels BEFORE LoadMotorConfiguration")
            dotnet_dump_channel(ch1, "ch1 BEFORE")
            dotnet_dump_channel(ch2, "ch2 BEFORE")
            dotnet_read_motor_params(ch1, "ch1 BEFORE")
            dotnet_read_motor_params(ch2, "ch2 BEFORE")

            # LoadMotorConfiguration — THE CRITICAL CALL
            # This writes StepsPerRev=200, GearboxRatio=1, Pitch=1 to firmware
            sub("A2: LoadMotorConfiguration ch1 (UseFileSettings)")
            for opt_name in ['UseFileSettings', 'UseConfiguredSettings', 'UseDeviceSettings']:
                try:
                    from Thorlabs.MotionControl.DeviceManagerCLI import DeviceSettingsUseOptionType
                    opt = getattr(DeviceSettingsUseOptionType, opt_name)
                    log.info(f"  ch1.LoadMotorConfiguration({SERIAL}, {opt_name})...")
                    ch1.LoadMotorConfiguration(SERIAL, opt)
                    time.sleep(3)
                    log.info(f"  ch1 LoadMotorConfiguration OK ({opt_name})!")
                    break
                except Exception as e:
                    err_str = str(e)[:120]
                    log.info(f"  {opt_name}: {err_str}")
            else:
                log.warning("  ch1 LoadMotorConfiguration FAILED with all options")

            sub("A2b: LoadMotorConfiguration ch2 (UseFileSettings)")
            for opt_name in ['UseFileSettings', 'UseConfiguredSettings', 'UseDeviceSettings']:
                try:
                    from Thorlabs.MotionControl.DeviceManagerCLI import DeviceSettingsUseOptionType
                    opt = getattr(DeviceSettingsUseOptionType, opt_name)
                    log.info(f"  ch2.LoadMotorConfiguration({SERIAL}, {opt_name})...")
                    ch2.LoadMotorConfiguration(SERIAL, opt)
                    time.sleep(3)
                    log.info(f"  ch2 LoadMotorConfiguration OK ({opt_name})!")
                    break
                except Exception as e:
                    err_str = str(e)[:120]
                    log.info(f"  {opt_name}: {err_str}")
            else:
                log.warning("  ch2 LoadMotorConfiguration FAILED with all options")

            sub("A3: Dump channels AFTER LoadMotorConfiguration")
            dotnet_dump_channel(ch1, "ch1 AFTER")
            dotnet_dump_channel(ch2, "ch2 AFTER")
            dotnet_read_motor_params(ch1, "ch1 AFTER")
            dotnet_read_motor_params(ch2, "ch2 AFTER")

            # Enable channels
            sub("A4: EnableDevice + StartPolling")
            for ch_num, ch_obj in [(1, ch1), (2, ch2)]:
                try:
                    log.info(f"  ch{ch_num}: EnableDevice()...")
                    ch_obj.EnableDevice()
                    time.sleep(1)
                    log.info(f"  ch{ch_num}: StartPolling(250)...")
                    ch_obj.StartPolling(250)
                    time.sleep(1)
                    log.info(f"  ch{ch_num}: IsEnabled={ch_obj.IsEnabled}, State={ch_obj.State}")
                except Exception as e:
                    log.warning(f"  ch{ch_num} enable error: {e}")

            # ══════════════════════════════════════════════════════
            # PHASE B: .NET API MOVEMENT TEST
            # ══════════════════════════════════════════════════════
            sec("PHASE B: .NET API MOVEMENT TEST")

            for ch_num, ch_obj in [(1, ch1), (2, ch2)]:
                sub(f"B1: ch{ch_num} .NET MoveRelative +20 steps (=40um)")
                steps_40um = int(40.0 / ENCODER_STEP)  # =20 steps
                delta = dotnet_test_move(ch_obj, steps_40um, f"ch{ch_num}")
                if delta is not None:
                    ok = abs(delta - steps_40um) <= 5
                    log.info(f"  ch{ch_num} +40um: delta={delta} expected={steps_40um} -> {'PASS' if ok else 'FAIL'}")
                    summary.append({"label": f".NET ch{ch_num} +40um", "expected": steps_40um, "got": delta, "pass": ok})
                else:
                    summary.append({"label": f".NET ch{ch_num} +40um", "expected": steps_40um, "got": -999, "pass": False})

                sub(f"B2: ch{ch_num} .NET MoveRelative -20 steps (=-40um)")
                delta2 = dotnet_test_move(ch_obj, -steps_40um, f"ch{ch_num} rev")
                if delta2 is not None:
                    ok2 = abs(delta2 - (-steps_40um)) <= 5
                    log.info(f"  ch{ch_num} -40um: delta={delta2} expected={-steps_40um} -> {'PASS' if ok2 else 'FAIL'}")
                    summary.append({"label": f".NET ch{ch_num} -40um", "expected": -steps_40um, "got": delta2, "pass": ok2})
                else:
                    summary.append({"label": f".NET ch{ch_num} -40um", "expected": -steps_40um, "got": -999, "pass": False})

            # ══════════════════════════════════════════════════════
            # PHASE C: Disconnect .NET, open C API, test
            # ══════════════════════════════════════════════════════
            sec("PHASE C: DISCONNECT .NET, TEST C API")

            sub("C0: StopPolling + Disconnect .NET")
            try:
                ch1.StopPolling()
                ch2.StopPolling()
                time.sleep(0.5)
                device.Disconnect()
                time.sleep(3)
                log.info("  .NET Disconnected OK")
            except Exception as e:
                log.warning(f"  .NET disconnect error: {e}")

            # Force cleanup .NET device
            try:
                del ch1, ch2, device
                import gc; gc.collect()
                time.sleep(2)
            except Exception:
                pass

            if bsm and bsm.DLL_AVAILABLE:
                sub("C1: Open C API")
                if c_open():
                    n = bsm.SBC_GetNumChannels(ser())
                    log.info(f"  NumChannels: {n}")

                    for ch_num in [c_short(1), c_short(2)]:
                        ch_label = f"ch{ch_num.value}"
                        sub(f"C2: {ch_label} C API dump after .NET init")
                        bsm.SBC_StartPolling(ser(), ch_num, c_int(250))
                        time.sleep(1)
                        c_dump(ch_num, f"{ch_label} C API after .NET")

                        # Read motor params via C API to verify they were written
                        try:
                            p1 = c_double(); p2 = c_double(); p3 = c_double()
                            err = bsm.SBC_GetMotorParamsExt(ser(), ch_num, byref(p1), byref(p2), byref(p3))
                            log.info(f"  {ch_label} SBC_GetMotorParamsExt: err={err} StepsPerRev={p1.value} GearboxRatio={p2.value} Pitch={p3.value}")
                        except Exception as e:
                            log.info(f"  {ch_label} GetMotorParamsExt error: {e}")

                        # Read power params
                        try:
                            pp = bsm.MOT_PowerParameters()
                            bsm.SBC_RequestPowerParams(ser(), ch_num); time.sleep(0.05)
                            bsm.SBC_GetPowerParams(ser(), ch_num, byref(pp))
                            log.info(f"  {ch_label} PowerParams: rest={pp.restPercentage}% move={pp.movePercentage}%")
                        except Exception as e:
                            log.info(f"  {ch_label} GetPowerParams error: {e}")

                    sub("C3: C API Movement test ch2")
                    ch = c_short(2)
                    bsm.SBC_StopImmediate(ser(), ch); time.sleep(0.3)
                    bsm.SBC_SetPositionCounter(ser(), ch, c_long(0)); time.sleep(0.5)
                    c_dump(ch, "before move")

                    c_roundtrip(40.0, " after .NET")
                    c_roundtrip(40.0, " after .NET RT2")

                    c_dump(ch, "FINAL")
                    c_close()
                else:
                    log.warning("  C API SBC_Open FAILED after .NET disconnect")
                    summary.append({"label": "C API reopen", "expected": 0, "got": -1, "pass": False})
            else:
                log.warning("  C API DLL not available")

        else:
            log.warning("  .NET init failed — cannot test")

        # ══════════════════════════════════════════════════════
        # SUMMARY
        # ══════════════════════════════════════════════════════
        sec("SUMMARY")
        if summary:
            log.info(f"  {'Test':<35} {'Exp':>8} {'Got':>8} {'Result':>8}")
            log.info(f"  {'-'*35} {'-'*8} {'-'*8} {'-'*8}")
            for r in summary:
                log.info(f"  {r['label']:<35} {r['expected']:>8} {r['got']:>8} {'PASS' if r['pass'] else 'FAIL':>8}")
            total = len(summary); passed = sum(1 for r in summary if r['pass'])
            log.info(f"\n  {passed}/{total} PASSED")
        else:
            log.info("  No tests completed")

        return 0

    except Exception as e:
        log.error(f"FATAL: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
