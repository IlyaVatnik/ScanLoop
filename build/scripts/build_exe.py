"""
build_exe.py — PyInstaller build engine for ScanLoop.
Reads settings from build_config.py, auto-installs deps via venv,
logs errors with suggested fixes.
"""

import os
import sys
import re
import shutil
import subprocess
import glob
import threading
import time
import zipfile
from datetime import datetime

import build_config as cfg


# ── Helpers ───────────────────────────────────────────────────

def section(label):
    print("\n" + "=" * 55)
    print("  " + label)
    print("=" * 55)


def ok(msg):
    print("  [OK] " + msg)


def warn(msg):
    print("  [!] " + msg)


def fail(msg):
    print("  [FAIL] " + msg)


# ── Error patterns & suggestions ─────────────────────────────

_ERROR_DB = [
    (re.compile(r"No module named '([^']+)'"),
     "Module '{0}' is missing. Try: pip install {0}"),
    (re.compile(r"DLL load failed(?: while importing ([^:]+))?"),
     "DLL load failed for '{0}'. If this is a Thorlabs DLL, install Kinesis from:\n"
     "       " + cfg.KINESIS_DOWNLOAD_URL),
    (re.compile(r"Failed to import '([^']+)'"),
     "Could not import '{0}'. Check if it's installed or vendored."),
    (re.compile(r"Cannot find existing PyQt5"),
     "PyQt5 not found. Install: pip install PyQt5"),
    (re.compile(r"WARNING.*hook-(\w+)"),
     "PyInstaller hook for '{0}' may have issues. Try: pip install --upgrade {0}"),
]


def suggest_fixes(raw_logs):
    seen = set()
    for line in raw_logs:
        for pattern, tip in _ERROR_DB:
            m = pattern.search(line)
            if m:
                key = pattern.pattern + m.group(1) if m.lastindex else pattern.pattern
                if key in seen:
                    continue
                seen.add(key)
                print("  ! " + tip.format(*m.groups()))


# ── Build log ─────────────────────────────────────────────────

def append_log(version, status, duration=None, extra=""):
    path = os.path.join(cfg.PROJECT_DIR, cfg.LOG_FILE)
    try:
        with open(path, 'a', encoding='utf-8') as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] v{version}_{cfg.APP_PREFIX} | {status}")
            if duration:
                f.write(f" | {duration:.0f}s")
            f.write("\n")
            if extra:
                f.write("  " + extra.replace("\n", "\n  ") + "\n")
    except IOError:
        pass


# ── Validation ───────────────────────────────────────────────

def validate():
    issues = []
    if not os.path.exists(cfg.MAIN_ENTRY):
        issues.append(("error", "main.py not found at: " + cfg.MAIN_ENTRY))
    for name in cfg.CONFIG_FILES:
        path = os.path.join(cfg.PROJECT_DIR, name)
        if not os.path.exists(path):
            issues.append(("warn", "Config file not found: " + name))
    if cfg.KINESIS_PATH:
        ok("Thorlabs Kinesis found at: " + cfg.KINESIS_PATH)
    else:
        warn("Thorlabs Kinesis not found in standard locations.")
        for _cand in cfg.KINESIS_CANDIDATES:
            kc_dll = os.path.join(_cand, 'Thorlabs.MotionControl.KCube.DCServo.dll')
            dm_dll = os.path.join(_cand, 'Thorlabs.MotionControl.DeviceManager.dll')
            warn(f"  Checked: {_cand} (KCube={os.path.exists(kc_dll)}, DeviceMgr={os.path.exists(dm_dll)})")
        if os.path.exists(cfg.KINESIS_USER_PATH_FILE):
            with open(cfg.KINESIS_USER_PATH_FILE, 'r') as f:
                saved_path = f.read().strip()
            warn(f"  User path file exists: {saved_path} (valid={os.path.exists(os.path.join(saved_path, 'Thorlabs.MotionControl.KCube.DCServo.dll')) if saved_path else False})")
        warn("  Download: " + cfg.KINESIS_DOWNLOAD_URL)
        warn("  Thorlabs stages will NOT work in the built EXE.")
    if os.path.exists(os.path.join(cfg.PROJECT_DIR, 'build_version.txt')):
        warn("Old build_version.txt detected in project root — remove it.")
    return issues


# ── Auto-search Kinesis ────────────────────────────────────────

def _auto_search_kinesis():
    drives = []
    for c in range(67, 91):
        drive = f"{chr(c)}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    if not drives:
        print("  Нет доступных дисков для поиска.")
        return None

    skip_dirs = {'Windows', '$Recycle.Bin', 'System Volume Information',
                 'ProgramData', 'AppData', 'node_modules', 'venv',
                 '.git', '__pycache__'}
    target_files = ['Thorlabs.MotionControl.KCube.DCServo.dll',
                    'Thorlabs.MotionControl.DeviceManager.dll']
    total = len(drives)

    try:
        for idx, drive in enumerate(drives, 1):
            print(f"  [{idx}/{total}] Сканируется {drive} ...")
            for root, dirs, files in os.walk(drive):
                dirs[:] = [d for d in dirs
                           if d not in skip_dirs
                           and not d.lower().startswith('windows')]
                if any(f in files for f in target_files):
                    if all(os.path.exists(os.path.join(root, tf)) for tf in target_files):
                        print(f"\n  Найдено: {root}")
                        yn = input("  Использовать этот путь? (y/n): ").strip().lower()
                        if yn in ('y', 'д', 'yes'):
                            return root
                        else:
                            print("  Поиск продолжается...")
    except KeyboardInterrupt:
        print("\n  Поиск прерван пользователем.")
    return None


def prompt_kinesis():
    if cfg.KINESIS_PATH:
        return
    print("\n  Thorlabs Kinesis не обнаружен автоматически.")
    while True:
        print("  Выберите опцию:")
        print("    0) Отменить сборку (откат изменений)")
        print("    1) Ввести путь вручную")
        print("    2) Показать ссылку для скачивания")
        print("    3) Продолжить без Thorlabs")
        print("    4) Найти самостоятельно (потребуется много времени)")
        try:
            choice = input("  Ваш выбор (0/1/2/3/4): ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "3"
        if choice == "0":
            v = cfg.read_version()
            if v > 1:
                cfg.write_version(v - 1)
                ok(f"Версия откачена: {v} -> {v - 1}")
            warn("  Сборка отменена пользователем.")
            sys.exit(0)
        elif choice == "1":
            try:
                user_path = input("  Путь к Kinesis (или Enter для возврата): ").strip()
            except (EOFError, KeyboardInterrupt):
                continue
            if not user_path:
                continue
            test_dll = os.path.join(user_path, 'Thorlabs.MotionControl.KCube.DCServo.dll')
            if os.path.exists(test_dll):
                cfg.save_kinesis_path(user_path)
                cfg.KINESIS_PATH = user_path
                ok(f"Путь к Kinesis сохранён: {cfg.KINESIS_USER_PATH_FILE}")
                return
            else:
                warn(f"  DLL не найдена по пути '{user_path}'. Проверьте путь и попробуйте снова.")
                continue
        elif choice == "2":
            print(f"  Скачать Kinesis: {cfg.KINESIS_DOWNLOAD_URL}")
            print("  Установите, затем перезапустите сборку.")
            continue
        elif choice == "3":
            warn("  Продолжение без Thorlabs Kinesis.")
            return
        elif choice == "4":
            path = _auto_search_kinesis()
            if path:
                cfg.save_kinesis_path(path)
                cfg.KINESIS_PATH = path
                ok(f"Путь к Kinesis сохранён: {cfg.KINESIS_USER_PATH_FILE}")
                return
            else:
                print("  Kinesis не найден. Возврат в меню.")
                continue
        else:
            warn("  Неверный выбор. Введите 0, 1, 2, 3 или 4.")


# ── PyInstaller command ──────────────────────────────────────

PYI_WORK_DIR = os.path.join('build', '_pyi')

_QT_PLUGINS_ADDED = False


def _fix_qt_plugins():
    global _QT_PLUGINS_ADDED
    if _QT_PLUGINS_ADDED:
        return None
    try:
        from PyInstaller.utils.hooks.qt import QtLibraryInfo
        info = QtLibraryInfo('PyQt5')
        auto_path = info.location.get('PluginsPath', '')
        if auto_path and os.path.isdir(auto_path):
            _QT_PLUGINS_ADDED = True
            return None
    except Exception:
        pass
    # Auto-detected path is broken (e.g. Cyrillic corrupted to '?').
    # Find it manually via the installed PyQt5 package.
    try:
        import PyQt5
        pkg_dir = os.path.dirname(PyQt5.__file__)
        for candidate in ['Qt5', 'Qt']:
            manual = os.path.join(pkg_dir, candidate, 'plugins')
            if os.path.isdir(manual):
                _QT_PLUGINS_ADDED = True
                return manual
    except Exception:
        pass
    return None


_QT_FIXED = False


def _fix_qt_plugins():
    global _QT_FIXED
    if _QT_FIXED:
        return True
    # Try to find correct plugins path manually
    manual_plugins = None
    try:
        import PyQt5
        pkg_dir = os.path.dirname(PyQt5.__file__)
        for candidate in ['Qt5', 'Qt']:
            manual = os.path.join(pkg_dir, candidate, 'plugins')
            if os.path.isdir(manual):
                manual_plugins = manual
                break
    except Exception:
        pass
    if not manual_plugins:
        _QT_FIXED = True
        return True
    # Patch PyInstaller's QtLibraryInfo singleton to fix the broken PluginsPath
    try:
        from PyInstaller.utils.hooks.qt import pyqt5_library_info
        # Force-load Qt info (first access triggers _load_qt_info)
        _ = pyqt5_library_info.version
        auto = pyqt5_library_info.location.get('PluginsPath', '')
        if auto and os.path.isdir(auto):
            _QT_FIXED = True
            return True
        # Path is broken (Cyrillic -> '?'); fix it in-place
        pyqt5_library_info.location['PluginsPath'] = manual_plugins
        # Also fix related paths that might share the corruption
        for key in list(pyqt5_library_info.location.keys()):
            old = pyqt5_library_info.location[key]
            if '?' in old:
                fixed = old.replace('?', '')  # strip corrupted chars
                # Rebuild from known-good prefix
                pyqt5_library_info.location[key] = os.path.join(
                    os.path.dirname(manual_plugins), os.path.basename(old)
                ).replace('/', '\\')
        _QT_FIXED = True
        ok(f"Qt PluginsPath patched: {manual_plugins}")
        return True
    except Exception as e:
        warn(f"Could not patch Qt plugins path: {e}")
        _QT_FIXED = True
        return True


def _patch_pyi_qt():
    """Run once inside the PyInstaller subprocess to fix Qt plugin path."""
    import os, sys, pathlib
    try:
        import PyQt5
        pkg_dir = os.path.dirname(PyQt5.__file__)
        for candidate in ['Qt5', 'Qt']:
            manual = os.path.join(pkg_dir, candidate, 'plugins')
            if os.path.isdir(manual):
                from PyInstaller.utils.hooks.qt import pyqt5_library_info
                _ = pyqt5_library_info.version  # trigger load
                if not os.path.isdir(pyqt5_library_info.location.get('PluginsPath', '')):
                    prefix = os.path.dirname(manual)
                    bin_path = os.path.join(prefix, 'bin')
                    # Patch location dict
                    pyqt5_library_info.location['PluginsPath'] = manual
                    pyqt5_library_info.location['PrefixPath'] = prefix
                    pyqt5_library_info.location['BinariesPath'] = bin_path
                    pyqt5_library_info.location['LibrariesPath'] = bin_path
                    pyqt5_library_info.location['LibraryExecutablesPath'] = bin_path
                    pyqt5_library_info.location['TranslationsPath'] = os.path.join(prefix, 'translations')
                    pyqt5_library_info.location['DataPath'] = prefix
                    # Also patch the resolved Path object that _load_info() cached
                    pyqt5_library_info.qt_lib_dir = pathlib.Path(bin_path).resolve()
                break
    except Exception:
        pass


def _build_wrapper_script():
    """Generate a wrapper .py that patches PyInstaller's Qt info then runs PyInstaller."""
    import inspect
    wrapper = os.path.join(cfg.PROJECT_DIR, 'build', '_pyi', '_qt_patch_wrapper.py')
    os.makedirs(os.path.dirname(wrapper), exist_ok=True)
    patch_src = inspect.getsource(_patch_pyi_qt)
    # Strip the decorator/def to get just the body
    body = '\n'.join(patch_src.split('\n')[1:])
    with open(wrapper, 'w', encoding='utf-8') as f:
        f.write("# Auto-generated Qt plugin path patch\n")
        f.write("import os, sys\n")
        f.write("os.environ['QT_PLUGIN_PATH'] = ''  # prevent Qt from using cached bad path\n")
        f.write("try:\n")
        for line in body.split('\n'):
            if line.strip():
                f.write(line + '\n')
        f.write("except Exception:\n")
        f.write("    pass\n")
        f.write("from PyInstaller.__main__ import run\n")
        f.write("sys.exit(run())\n")
    return wrapper


def build_command(app_name):
    _fix_qt_plugins()
    wrapper = _build_wrapper_script()
    cmd = [
        sys.executable, wrapper, "--name", app_name,
        "--onedir", "--windowed",
        "--workpath", PYI_WORK_DIR,
        "--specpath", PYI_WORK_DIR,
        "--paths", cfg.PROJECT_DIR,
        "--paths", os.path.join(cfg.PROJECT_DIR, "Hardware", "Stages"),
        "--paths", cfg.VENDOR_DIR,
    ]
    for mod in cfg.COLLECT_MODULES:
        cmd += ["--collect-submodules", mod]
    for mod in cfg.HIDDEN_IMPORTS:
        cmd += ["--hidden-import", mod]
    for mod in cfg.EXCLUDE_MODULES:
        cmd += ["--exclude-module", mod]

    # Stage DLLs
    cmd += [
        f"--add-data={cfg.STAND_DIR};Hardware/Stages/Standa",
        f"--add-data={cfg.LBTEK_DIR};Hardware/Stages/LBTEK/LBTEKx64",
    ]

    # Kinesis DLLs
    if cfg.KINESIS_PATH:
        for dll_name in cfg.KINESIS_DLL_NAMES:
            dll_path = os.path.join(cfg.KINESIS_PATH, dll_name)
            if os.path.exists(dll_path):
                cmd += [f"--add-binary={dll_path};."]
            else:
                warn("DLL not found (skipped): " + dll_name)

    # Config files
    for name in cfg.CONFIG_FILES:
        path = os.path.join(cfg.PROJECT_DIR, name)
        if os.path.exists(path):
            cmd += [f"--add-data={path};."]

    cmd += ["main.py"]
    return cmd, {}


# ── Spinner runner ───────────────────────────────────────────

_PHASES = {
    "Building Analysis": "Analysis...",
    "Analyzing modules for base": "Building base modules...",
    "hook-numpy": "NumPy...",
    "hook-scipy": "SciPy...",
    "hook-matplotlib": "Matplotlib...",
    "hook-PyQt5": "PyQt5...",
    "hook-pickle": "Pickle...",
    "post-graph stage": "Finishing dependency analysis...",
    "Building PYZ": "Compressing Python code...",
    "Building EXE": "Creating executable...",
    "Building COLLECT": "Copying files into build...",
}


def run_pyinstaller(cmd, env_extras=None):
    env = os.environ.copy()
    if env_extras:
        env.update(env_extras)
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, encoding='utf-8', errors='replace',
        env=env
    )
    phases = dict(_PHASES)
    total = len(phases)
    state = {'running': True, 'desc': "Initializing...", 'pct': 0}
    raw_logs = []

    def spinner():
        chars = '|/-\\'
        i = 0
        while state['running']:
            bar = '#' * (state['pct'] * total // 100) if state['pct'] else ''
            dots = '.' * (total - len(bar))
            sys.stdout.write(
                f"\r[{bar}{dots}] {state['pct']:3d}% {chars[i % 4]} | {state['desc']}"
            )
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)

    t = threading.Thread(target=spinner, daemon=True)
    t.start()
    done = 0
    for line in process.stdout:
        raw_logs.append(line)
        for key, desc in list(phases.items()):
            if key in line:
                done += 1
                state['pct'] = int(done * 100 / total)
                state['desc'] = desc
                del phases[key]
                break
    process.wait()
    state['running'] = False
    t.join()
    bar = '#' * total
    sys.stdout.write(f"\r[{bar}] 100% | Build complete!\n")
    sys.stdout.flush()
    return process.returncode, raw_logs


# ── Post-build steps ─────────────────────────────────────────

def post_build(dist_dir, app_name):
    exe_path = os.path.join(dist_dir, app_name + ".exe")
    if not os.path.exists(exe_path):
        fail("EXE not created: " + exe_path)
        return False
    size_mb = os.path.getsize(exe_path) / 1024 / 1024
    ok(f"EXE: {size_mb:.2f} MB")

    for folder in ['ProcessedData', 'SpectralData', 'SpectralBinData', 'TimeDomainData']:
        os.makedirs(os.path.join(dist_dir, folder), exist_ok=True)

    for name in cfg.CONFIG_FILES:
        src = os.path.join(cfg.PROJECT_DIR, name)
        dst = os.path.join(dist_dir, name)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)

    # Vendor packages
    vendor_dst = os.path.join(dist_dir, '_internal')
    if os.path.exists(cfg.VENDOR_DIR):
        for item in os.listdir(cfg.VENDOR_DIR):
            s = os.path.join(cfg.VENDOR_DIR, item)
            d = os.path.join(vendor_dst, item)
            if os.path.isdir(s) and not os.path.exists(d) and item != '__pycache__':
                shutil.copytree(s, d, ignore=shutil.ignore_patterns('__pycache__'))
            elif os.path.isfile(s) and not os.path.exists(d) and item.endswith('.py'):
                shutil.copy2(s, d)

    # .pkl3d / .pkl
    pkl_src = os.path.join(cfg.PROJECT_DIR, 'ProcessedData')
    pkl_dst = os.path.join(dist_dir, 'ProcessedData')
    if os.path.exists(pkl_src):
        for item in os.listdir(pkl_src):
            s = os.path.join(pkl_src, item)
            d = os.path.join(pkl_dst, item)
            if os.path.isfile(s) and not os.path.exists(d) and item.endswith(('.pkl3d', '.pkl')):
                shutil.copy2(s, d)

    return True


def create_zip(dist_dir, app_name):
    zip_name = os.path.join(cfg.PROJECT_DIR, 'dist', app_name + ".zip")
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for d in dirs:
                p = os.path.join(root, d)
                zipf.write(p, os.path.relpath(p, os.path.join(dist_dir, '..')))
            for f in files:
                p = os.path.join(root, f)
                zipf.write(p, os.path.relpath(p, os.path.join(dist_dir, '..')))
    size_mb = os.path.getsize(zip_name) / 1024 / 1024
    ok(f"ZIP: {zip_name} ({size_mb:.2f} MB)")


# ── Main ─────────────────────────────────────────────────────

def main():
    start = time.time()

    section("Build Configuration")
    version = cfg.next_version()
    app_name = f"v{version}_{cfg.APP_PREFIX}"
    print(f"  App:      {app_name}")
    print(f"  User:     {cfg.USER_SLUG}")
    print(f"  Python:   {sys.executable}")
    print(f"  Kinesis:  {cfg.KINESIS_PATH or '(not found)'}")

    section("Project Validation")
    issues = validate()
    if any(sev == "error" for sev, _ in issues):
        for sev, msg in issues:
            (fail if sev == "error" else warn)(msg)
        sys.exit(1)

    prompt_kinesis()

    section("Cleaning previous build")
    dist_root = os.path.join(cfg.PROJECT_DIR, 'dist')
    if os.path.exists(dist_root):
        shutil.rmtree(dist_root)
        ok("dist/ cleaned")
    if os.path.exists(PYI_WORK_DIR):
        shutil.rmtree(PYI_WORK_DIR, ignore_errors=True)
        ok("build/_pyi/ cleaned")
    for spec in glob.glob(os.path.join(PYI_WORK_DIR, '*.spec')):
        os.remove(spec)

    section("Building with PyInstaller")
    cmd, env_extras = build_command(app_name)
    retcode, raw_logs = run_pyinstaller(cmd, env_extras)

    if retcode != 0:
        fail(f"PyInstaller exited with code {retcode}")
        print("\n  Suggestions:")
        suggest_fixes(raw_logs)
        print("\n  Last log lines:")
        for line in raw_logs[-20:]:
            safe = line.rstrip().encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding, errors='replace')
            print("    " + safe)
        log_extra = "\n".join(raw_logs[-5:]).rstrip()
        log_safe = log_extra.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        append_log(version, "FAILED", extra=log_safe)
        sys.exit(1)

    dist_dir = os.path.join(cfg.PROJECT_DIR, 'dist', app_name)

    section("Post-build")
    if not post_build(dist_dir, app_name):
        append_log(version, "FAILED (post-build)")
        sys.exit(1)

    section("Archive")
    create_zip(dist_dir, app_name)

    elapsed = time.time() - start
    ok(f"Build finished in {elapsed:.0f}s")
    print(f"\n  Output: {dist_dir}")

    append_log(version, "SUCCESS", duration=elapsed,
               extra=f"Path: dist/{app_name}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        err_path = os.path.join(cfg.PROJECT_DIR, 'build', 'scripts', 'build_crash.log')
        with open(err_path, 'w', encoding='utf-8') as f:
            traceback.print_exc(file=f)
        print(f"\n[FATAL] Build crashed. Details saved to {err_path}")
        sys.exit(1)
