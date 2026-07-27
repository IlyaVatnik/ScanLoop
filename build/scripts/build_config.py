"""
build_config.py — self-initializing build configuration for ScanLoop.
Auto-detects environment, generates build_exe.bat, provides settings to build_exe.py.
"""

import os
import sys

# ── Transliteration ──────────────────────────────────────────

_CYRILLIC_MAP = {
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G',
    'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh',
    'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K',
    'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
    'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
    'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts',
    'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': '',
    'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu',
    'Я': 'Ya',
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g',
    'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
    'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '',
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
    'я': 'ya',
}


def _transliterate(text: str) -> str:
    result = []
    for ch in text:
        result.append(_CYRILLIC_MAP.get(ch, ch))
    return ''.join(result)


def identity_slug(value: str) -> str:
    s = _transliterate(value.strip())
    while s and not s[0].isalnum():
        s = s[1:]
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    return s or 'Unknown'


# ── Identity ──────────────────────────────────────────────────

RAW_USERNAME = os.environ.get('USERNAME', os.environ.get('USER', 'Unknown'))
COMPUTERNAME = os.environ.get('COMPUTERNAME', 'UNKNOWN')
USER_SLUG = identity_slug(RAW_USERNAME) + '_' + COMPUTERNAME

APP_PREFIX = 'ScanLoop_' + USER_SLUG
VERSION_FILE = 'build/scripts/build_version_' + USER_SLUG + '.txt'
LOG_FILE = 'build/scripts/build_log_' + USER_SLUG + '.txt'

# ── Project paths ────────────────────────────────────────────

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.normpath(os.path.join(_SCRIPT_DIR, '..', '..'))
MAIN_ENTRY = os.path.join(PROJECT_DIR, 'main.py')
VENDOR_DIR = os.path.join(PROJECT_DIR, 'vendor_pkgs')
CONFIG_FILES = [
    'config_interrogator.json',
    'plotting_parameters.txt',
    'ZeroPosition.txt',
    'PiezoStageStartPosition.json',
]
STAND_DIR = os.path.join(PROJECT_DIR, 'Hardware', 'Stages', 'Standa')
LBTEK_DIR = os.path.join(PROJECT_DIR, 'Hardware', 'Stages', 'LBTEK', 'LBTEKx64')

# ── Kinesis detection ────────────────────────────────────────

KINESIS_CANDIDATES = [
    r"C:\Program Files\Thorlabs\Kinesis",
    r"C:\Program Files (x86)\Thorlabs\Kinesis",
]
KINESIS_DLL_NAMES = [
    "Thorlabs.MotionControl.KCube.DCServo.dll",
    "Thorlabs.MotionControl.Benchtop.StepperMotor.dll",
    "Thorlabs.MotionControl.DeviceManager.dll",
    "Thorlabs.MotionControl.PrivateInternal.dll",
    "ftd2xx.dll",
    "Thorlabs.MotionControl.FTD2xx_Net.dll",
]
KINESIS_DOWNLOAD_URL = "https://www.thorlabs.com/motion-controllers-software-downloads"
KINESIS_USER_PATH_FILE = os.path.join(_SCRIPT_DIR, 'kinesis_user_path.txt')

KINESIS_PATH = None


def _resolve_kinesis() -> str | None:
    # Check standard install locations
    for _cand in KINESIS_CANDIDATES:
        kc_dll = os.path.join(_cand, 'Thorlabs.MotionControl.KCube.DCServo.dll')
        dm_dll = os.path.join(_cand, 'Thorlabs.MotionControl.DeviceManager.dll')
        if os.path.exists(kc_dll) and os.path.exists(dm_dll):
            return _cand
    # Fallback: user-saved path from previous manual entry
    if os.path.exists(KINESIS_USER_PATH_FILE):
        try:
            with open(KINESIS_USER_PATH_FILE, 'r') as f:
                user_path = f.read().strip()
            if user_path:
                test_dll = os.path.join(user_path, 'Thorlabs.MotionControl.KCube.DCServo.dll')
                if os.path.exists(test_dll):
                    return user_path
        except (IOError, OSError):
            pass
    return None


def save_kinesis_path(path: str):
    path = path.strip().rstrip('\\')
    try:
        with open(KINESIS_USER_PATH_FILE, 'w') as f:
            f.write(path)
    except IOError as e:
        print(f"  [KINESIS] Could not save path: {e}")


KINESIS_PATH = _resolve_kinesis()

# ── PyInstaller parameters ───────────────────────────────────

COLLECT_MODULES = [
    "Common", "Windows_GUI", "Hardware", "Scripts",
    "Utils", "Logger", "Visualization", "Theory",
    "Hardware.Stages",
    "Hardware.Stages.Standa",
    "Hardware.Stages.LBTEK",
    "Hardware.PyApex",
    "Hardware.LaserLibs",
    "Windows_GUI.UIs",
]

HIDDEN_IMPORTS = [
    "Scripts.ScanningProcessOSA",
    "Scripts.ScanningProcessLaser",
    "Scripts.ScanningProcessScope",
    "Scripts.Analyzer",
    "Scripts.Spectral_processor",
    "Scripts.SNAP_experiment",
    "Scripts.OVA_signals",
    "Scripts.TD_processor",
    "Scripts.analyze_oscillogram",
    "Hardware.Stages.stages_manager",
    "Hardware.Stages.PIStages",
    "Hardware.Stages.PiezoStageE53D_serial",
    "Hardware.Stages.thorlabs_kinesis",
    "Hardware.Stages.thorlabs_kinesis.ext",
    "Hardware.Scanner",
    "Hardware.Config",
    "serial.tools.list_ports",
    "pipython",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.backends.backend_qt5",
    "pyvisa",
    "pyvisa_py",
    "pyusb",
    "libusb_package",
    "typing_extensions",
]

EXCLUDE_MODULES = ["PyQt6", "PySide6"]

# ── Version file management ──────────────────────────────────


def read_version() -> int:
    path = os.path.join(PROJECT_DIR, VERSION_FILE)
    try:
        with open(path, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 1


def write_version(version: int):
    path = os.path.join(PROJECT_DIR, VERSION_FILE)
    with open(path, 'w') as f:
        f.write(str(version))


def next_version() -> int:
    v = read_version()
    write_version(v + 1)
    return v + 1


if __name__ == '__main__':
    print("USER_SLUG:", USER_SLUG)
    print("APP_PREFIX:", APP_PREFIX)
    print("VERSION_FILE:", VERSION_FILE)
    print("LOG_FILE:", LOG_FILE)
    print("KINESIS_PATH:", KINESIS_PATH if KINESIS_PATH else "(not found)")
    print("KINESIS_USER_PATH_FILE:", KINESIS_USER_PATH_FILE)
