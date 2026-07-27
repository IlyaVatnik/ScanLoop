"""
Diagnostic BSM v12 — restPercentage recovery sweep
"""
import sys, os, time, logging, traceback
from datetime import datetime
from ctypes import c_short, c_int, c_uint, c_long, c_char_p, c_int16, byref
from ctypes import c_ushort as c_word

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "..", ".."))
from Hardware.Stages.thorlabs_kinesis import benchtop_stepper_motor as bsm

LOG_DIR = os.path.join(SCRIPT_DIR, "Logs"); os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, f"diagnostic_v12_{datetime.now():%Y-%m-%d_%H-%M-%S}.log")
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s", datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_path, encoding="utf-8")])
log = logging.getLogger("diag")

SERIAL = "70864299"; ENCODER_STEP = 0.002; summary = []
STATUS_BITS = {0x00000001:"FWD_HW_LIMIT",0x00000002:"REV_HW_LIMIT",0x00000004:"INMOTION_FWD",
    0x00000008:"INMOTION_REV",0x00000010:"FWD_SW_LIMIT",0x00000020:"REV_SW_LIMIT",
    0x00000040:"MOTOR_CONNECTED",0x00000080:"HOMING",0x00000100:"HOMED",0x00000200:"MOVING",
    0x00000400:"ENABLED",0x00000800:"DISABLED",0x00001000:"ERROR",0x00002000:"STALL",
    0x00004000:"TEMP_FAULT",0x00008000:"CURRENT_FOLD"}

def s(x): return x.value if hasattr(x,'value') else int(x)
def decode(bits): return " | ".join(n for m,n in STATUS_BITS.items() if bits & m) or "NONE"
def sec(t): log.info(f"\n{'='*60}\n  {t}\n{'='*60}")
def sub(t): log.info(f"\n--- {t} ---")
def ser(): return c_char_p(SERIAL.encode("utf-8"))
def open_bsm():
    bsm.TLI_BuildDeviceList()
    for i in range(1,4):
        if bsm.SBC_Open(ser())==0: time.sleep(0.3); return True
        log.warning(f"  SBC_Open attempt {i}/3"); time.sleep(1.0*i)
    log.error("  SBC_Open FAILED"); return False
def close_bsm():
    bsm.SBC_StopProfiled(ser(),c_short(1)); time.sleep(0.1)
    bsm.SBC_StopProfiled(ser(),c_short(2)); time.sleep(0.3)
    bsm.SBC_Close(ser()); time.sleep(1.0)
def pos(ch): bsm.SBC_RequestPosition(ser(),ch); time.sleep(0.01); return s(bsm.SBC_GetPosition(ser(),ch))
def status(ch): bsm.SBC_RequestStatusBits(ser(),ch); time.sleep(0.02); return s(bsm.SBC_GetStatusBits(ser(),ch))
def dump(ch,label=""):
    b=status(ch); p=pos(ch)
    log.info(f"  [{label}] Status=0x{b:08X}={decode(b)} Pos={p}({p*ENCODER_STEP:.4f}mm)"); return b
def poll(ch,timeout=30):
    t0=time.time(); last=None; st=0
    while time.time()-t0<timeout:
        time.sleep(0.05); v=pos(ch)
        if v==last: st+=1
        else: st=0; last=v
        if st>=10: return v
    log.warning(f"  poll timeout {timeout}s last={last}"); return last
def move(ch,um):
    steps=int((um/1000.0)/ENCODER_STEP); log.info(f"  move {um}um = {steps} steps")
    bsm.SBC_StartPolling(ser(),ch,c_int(100)); bsm.SBC_ClearMessageQueue(ser(),ch); time.sleep(0.1)
    bsm.SBC_SetMoveRelativeDistance(ser(),ch,c_int(steps)); err=bsm.SBC_MoveRelativeDistance(ser(),ch)
    log.info(f"  MoveRelative err={err}"); r=poll(ch); bsm.SBC_StopPolling(ser(),ch); return r,err
def read_power(ch,label=""):
    bsm.SBC_RequestPowerParams(ser(),ch); time.sleep(0.02); pp=bsm.MOT_PowerParameters()
    bsm.SBC_GetPowerParams(ser(),ch,byref(pp))
    log.info(f"  [{label}] rest={pp.restPercentage}% move={pp.movePercentage}%"); return pp.restPercentage,pp.movePercentage
def set_power(ch,rest,move):
    pp=bsm.MOT_PowerParameters(); pp.restPercentage=c_word(rest); pp.movePercentage=c_word(move)
    err=bsm.SBC_SetPowerParams(ser(),ch,byref(pp)); log.info(f"  SetPowerParams({rest}%/{move}%) -> err={err}"); time.sleep(0.1); return err
def persist(ch):
    for i in range(3):
        if bsm.SBC_PersistSettings(ser(),ch): log.info(f"  PersistSettings OK (attempt {i+1})"); return True
        time.sleep(1)
    log.warning("  PersistSettings FAILED"); return False
def do_roundtrip(dist_um, label=""):
    expected=int((dist_um/1000.0)/ENCODER_STEP); ch=c_short(2); before=pos(ch)
    sub(f"Move +{dist_um}um{label}"); move(ch,dist_um); after_p=pos(ch); d1=after_p-before
    ok1=abs(d1-expected)<=5; log.info(f"  +{dist_um}um: delta={d1} expected={expected} -> {'PASS' if ok1 else 'FAIL'}")
    summary.append({"label":f"+{dist_um}um{label}","expected":expected,"got":d1,"pass":ok1})
    sub(f"Move -{dist_um}um{label}"); move(ch,-dist_um); after_m=pos(ch); d2=after_m-after_p
    ok2=abs(d2-(-expected))<=5; log.info(f"  -{dist_um}um: delta={d2} expected={-expected} -> {'PASS' if ok2 else 'FAIL'}")
    summary.append({"label":f"-{dist_um}um{label}","expected":-expected,"got":d2,"pass":ok2}); time.sleep(0.3)

def main():
    try:
        sec(f"DIAGNOSTIC BSM v12 — restPercentage recovery — {datetime.now():%Y-%m-%d %H:%M:%S}")
        log.info(f"  Log: {log_path}")
        if not bsm or not bsm.DLL_AVAILABLE: log.error("BSM DLL not available"); return 1
        ch=c_short(2)

        sec("OPEN + STOP IMMEDIATE")
        if not open_bsm(): return 1
        bsm.SBC_StopImmediate(ser(),ch); time.sleep(0.3); dump(ch,"initial")

        sec("PHASE 1: SWEEP restPercentage")
        test_values=[0,6,10,20,50,100]; sweep_results=[]
        for target_rest in test_values:
            sub(f"Try rest={target_rest}%")
            set_power(ch,target_rest,target_rest); persist(ch); time.sleep(0.5)
            actual_rest,actual_move=read_power(ch,f"after rest={target_rest}%")
            match=(actual_rest==target_rest); sweep_results.append({"target":target_rest,"actual":actual_rest,"match":match})
            log.info(f"  -> {'MATCH' if match else 'MISMATCH'} (wrote {target_rest}, read {actual_rest})")

        sec("SWEEP RESULTS")
        log.info(f"  {'Target':>8} {'Actual':>8} {'Match':>8}")
        log.info(f"  {'-'*8} {'-'*8} {'-'*8}")
        for r in sweep_results: log.info(f"  {r['target']:>8} {r['actual']:>8} {'YES' if r['match'] else 'NO':>8}")

        best_rest=None
        for r in sweep_results:
            if r["match"]: best_rest=r["target"]; break
        if best_rest is None:
            log.warning("  NO VALUE MATCHED — EEPROM corruption irrecoverable via API")
            best_rest=6; log.info(f"  Using rest={best_rest}% anyway")
        else: log.info(f"  Best rest={best_rest}%")

        sec("PHASE 2: SET FINAL PowerParams")
        sub(f"Set PowerParams({best_rest}%/{best_rest}%)")
        set_power(ch,best_rest,best_rest); persist(ch); time.sleep(0.5)
        read_power(ch,"FINAL")
        sub("SetBacklash(0)"); bsm.SBC_SetBacklash(ser(),ch,c_long(0))
        sub("SetPositionCounter(0)"); bsm.SBC_StopImmediate(ser(),ch); time.sleep(0.3)
        e=bsm.SBC_SetPositionCounter(ser(),ch,c_long(0)); log.info(f"  -> err={e}"); time.sleep(1.0)
        dump(ch,"ready for moves")

        sec("PHASE 3: MOVES")
        sec("STEP 1: Single roundtrip 40um"); do_roundtrip(40.0)
        sec("STEP 2: 10 roundtrips 40um")
        for i in range(10): do_roundtrip(40.0, f" RT{i+1}")
        sec("STEP 3: Different distances")
        for dist in [10.0,20.0,50.0,100.0,200.0]: do_roundtrip(dist)
        sec("STEP 4: Stability 10s (no moves)")
        p0=pos(ch); log.info(f"  Start: {p0}")
        for t in range(10):
            time.sleep(1); p=pos(ch)
            log.info(f"  t={t+1}s: pos={p} drift={p-p0}" + (" OK" if p==p0 else ""))
        ok=abs(pos(ch)-p0)<=2
        summary.append({"label":"stability","expected":0,"got":pos(ch)-p0,"pass":ok})
        log.info(f"  Stability: {'PASS' if ok else 'FAIL'}")
        sec("STEP 5: Final status + PowerParams check"); dump(ch,"FINAL"); read_power(ch,"FINAL")
        close_bsm()

        sec("SUMMARY")
        log.info(f"  {'Test':<25} {'Exp':>8} {'Got':>8} {'Result':>8}")
        log.info(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*8}")
        for r in summary:
            log.info(f"  {r['label']:<25} {r['expected']:>8} {r['got']:>8} {'PASS' if r['pass'] else 'FAIL':>8}")
        total=len(summary); passed=sum(1 for r in summary if r['pass'])
        log.info(f"\n  {passed}/{total} PASSED"); return 0
    except Exception as e:
        log.error(f"FATAL: {e}\n{traceback.format_exc()}"); return 1
if __name__=="__main__": sys.exit(main())
