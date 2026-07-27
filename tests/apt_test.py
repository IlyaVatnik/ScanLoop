"""
APT API test for Thorlabs BSM — runs as subprocess to avoid Kinesis DLL conflict.
Usage: python apt_test.py <serial_number> <parent_log_path>
"""

import sys
import os
import time
import logging
from datetime import datetime
from ctypes import c_char_p, c_int, c_long, c_uint, byref, cdll

if len(sys.argv) < 3:
    print("Usage: python apt_test.py <serial_number> <parent_log_path>")
    sys.exit(1)

DEVICE_SERIAL = sys.argv[1]
PARENT_LOG = sys.argv[2]
LOG_DIR = os.path.dirname(PARENT_LOG)
log_path = os.path.join(LOG_DIR, f"apt_test_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_path, encoding="utf-8"),
    ],
)
log = logging.getLogger("apt")

ENCODER_STEP = 0.002

APT_DLL_PATHS = [
    os.path.join(os.environ.get("ProgramFiles", ""), "Thorlabs", "APT", "APT.dll"),
    os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Thorlabs", "APT", "APT.dll"),
]

apt = None


def load_apt():
    global apt
    for p in APT_DLL_PATHS:
        if os.path.exists(p):
            log.info(f"  Loading APT DLL: {p}")
            try:
                os.add_dll_directory(os.path.dirname(p))
            except AttributeError:
                pass
            apt = cdll.LoadLibrary(p)
            log.info(f"  APT DLL loaded successfully")
            return True
    log.warning("  APT DLL not found")
    return False


def sv(x):
    return x.value if hasattr(x, 'value') else int(x)


def main():
    log.info(f"APT test for device {DEVICE_SERIAL}")
    log.info(f"Parent log: {PARENT_LOG}")
    log.info(f"APT test log: {log_path}")

    if not load_apt():
        log.warning("  Cannot load APT DLL, skipping")
        return 1

    log.info("  Initializing APT...")
    err = apt.Init()
    log.info(f"  APT.Init -> {err}")

    serial_c = c_char_p(DEVICE_SERIAL.encode("utf-8"))
    log.info(f"  APT.InitHWDevice({DEVICE_SERIAL})...")
    err = apt.InitHWDevice(serial_c)
    log.info(f"  APT.InitHWDevice -> {err}")

    if err != 0:
        log.warning(f"  APT.InitHWDevice failed with err={err}")
        log.info("  Trying APT.MOT_LL InitialiseHWDevice...")
        try:
            err = apt.MOT_LL_InitialiseHWDevice(serial_c)
            log.info(f"  MOT_LL_InitialiseHWDevice -> {err}")
        except AttributeError:
            log.warning("  MOT_LL_InitialiseHWDevice not available")

    log.info("  Attempting to get status...")
    try:
        status = c_int()
        err = apt.MOT_LL_GetStatus(serial_c, byref(status))
        log.info(f"  MOT_LL_GetStatus -> err={err}, status={sv(status)}")
    except AttributeError:
        log.warning("  MOT_LL_GetStatus not available")

    log.info("  Closing APT...")
    try:
        apt.Close()
    except:
        pass

    log.info("  APT test complete")
    return 0


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
