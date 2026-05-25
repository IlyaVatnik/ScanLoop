# build_exe.py (Золотой стандарт, ИСПРАВЛЕННЫЙ)
import os, sys, shutil, subprocess, glob, threading, time

def get_and_update_version():
    version_file = 'build_version.txt'
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            try: version = int(f.read().strip())
            except ValueError: version = 19
    else: version = 19
    with open(version_file, 'w') as f: f.write(str(version + 1))
    return version

def main():
    print("=== НАЧАЛО СБОРКИ ПРОЕКТА ===")
    current_dir = os.getcwd()
    version = get_and_update_version()
    app_name = f"main_v{version}"
    print(f"Текущая версия сборки: {app_name}")
    
    # Очистка dist перед сборкой
    dist_dir = os.path.join(current_dir, 'dist')
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
        print(" -> dist очищен")
    if os.path.exists('build'):
        shutil.rmtree('build', ignore_errors=True)
    for spec_file in glob.glob("*.spec"):
        os.remove(spec_file)

    print(f"\nЗапуск PyInstaller для {app_name}...\n" + "-"*50)

    standa_path = os.path.join("Hardware", "Stages", "Standa")
    lbtek_path  = os.path.join("Hardware", "Stages", "LBTEK", "LBTEKx64")
    kinesis_path = r"C:\Program Files\Thorlabs\Kinesis"

    command = [
        sys.executable, "-m", "PyInstaller", "--name", app_name, "--onedir", "--windowed",
        "--paths", ".",
        "--paths", os.path.join("Hardware", "Stages"),  # для thorlabs_kinesis импорта
        "--paths", "vendor_pkgs",  # pyvisa, pipython и др. (установлены локально)

        # Все пакеты проекта
        "--collect-submodules", "Common",
        "--collect-submodules", "Windows_GUI",
        "--collect-submodules", "Hardware",
        "--collect-submodules", "Scripts",
        "--collect-submodules", "Utils",
        "--collect-submodules", "Logger",
        "--collect-submodules", "Visualization",
        "--collect-submodules", "Theory",

        # Вложенные пакеты (для надёжности)
        "--collect-submodules", "Hardware.Stages",
        "--collect-submodules", "Hardware.Stages.Standa",
        "--collect-submodules", "Hardware.Stages.LBTEK",
        "--collect-submodules", "Hardware.PyApex",
        "--collect-submodules", "Hardware.LaserLibs",
        "--collect-submodules", "Windows_GUI.UIs",

        # Явные hidden-imports (динамические / условные импорты)
        "--hidden-import", "Scripts.ScanningProcessOSA",
        "--hidden-import", "Scripts.ScanningProcessLaser",
        "--hidden-import", "Scripts.ScanningProcessScope",
        "--hidden-import", "Scripts.Analyzer",
        "--hidden-import", "Scripts.Spectral_processor",
        "--hidden-import", "Scripts.SNAP_experiment",
        "--hidden-import", "Scripts.OVA_signals",
        "--hidden-import", "Scripts.TD_processor",
        "--hidden-import", "Scripts.analyze_oscillogram",
        "--hidden-import", "Hardware.Stages.stages_manager",
        "--hidden-import", "Hardware.Stages.PIStages",
        "--hidden-import", "Hardware.Stages.PiezoStageE53D_serial",
        "--hidden-import", "Hardware.Scanner",
        "--hidden-import", "Hardware.Config",
        "--hidden-import", "serial.tools.list_ports",
        "--hidden-import", "pipython",

        # Matplotlib бэкенд (иначе нет графиков!)
        "--hidden-import", "matplotlib.backends.backend_qt5agg",
        "--hidden-import", "matplotlib.backends.backend_qt5",

        # PyVISA бэкенды
        "--hidden-import", "pyvisa",
        "--hidden-import", "pyvisa_py",
        "--hidden-import", "pyusb",
        "--hidden-import", "typing_extensions",

        # DLL столиков
        f"--add-data={standa_path};Hardware/Stages/Standa",
        f"--add-data={lbtek_path};Hardware/Stages/LBTEK/LBTEKx64",

        # Thorlabs Kinesis DLL (для KDC101, BSC201/BSC203)
        f"--add-binary={kinesis_path}\\Thorlabs.MotionControl.KCube.DCServo.dll;.",
        f"--add-binary={kinesis_path}\\Thorlabs.MotionControl.Benchtop.StepperMotor.dll;.",
        f"--add-binary={kinesis_path}\\Thorlabs.MotionControl.DeviceManager.dll;.",
        f"--add-binary={kinesis_path}\\Thorlabs.MotionControl.PrivateInternal.dll;.",
        f"--add-binary={kinesis_path}\\ftd2xx.dll;.",
        f"--add-binary={kinesis_path}\\Thorlabs.MotionControl.FTD2xx_Net.dll;.",

        # Конфиги (только существующие, чтобы избежать ошибок сборки)
        *[arg for f in ['config_interrogator.json', 'plotting_parameters.txt',
                         'ZeroPosition.txt', 'PiezoStageStartPosition.json']
          for arg in (f"--add-data={f};.",) if os.path.exists(f)],

        "--exclude-module", "PyQt6", "--exclude-module", "PySide6",
        "main.py"
    ]

    # --- ОДИН ЕДИНСТВЕННЫЙ БЛОК TRY...EXCEPT ---
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace')
        phases = {
            "Building Analysis": "Анализ структуры проекта...",
            "Analyzing modules for base": "Сбор базовых модулей Python...",
            "hook-numpy": "Подключение NumPy...",
            "hook-scipy": "Подключение SciPy...",
            "hook-matplotlib": "Подключение Matplotlib...",
            "hook-PyQt5": "Подключение PyQt5...",
            "hook-pickle": "Подключение Pickle...",
            "post-graph stage": "Завершение анализа зависимостей...",
            "Building PYZ": "Сжатие Python-кода...",
            "Building EXE": "Создание исполняемого файла...",
            "Building COLLECT": "Копирование файлов в сборку..."
        }
        total_phases, ui_state = len(phases), {'is_running': True, 'desc': "Инициализация..."}
        def spinner_task():
            spinner_chars = ['|', '/', '-', '\\']
            idx = 0
            while ui_state['is_running']:
                sys.stdout.write(f"\r{ui_state.get('bar', '')} {ui_state.get('percent', 0):3d}% {spinner_chars[idx % 4]} | {ui_state['desc']}")
                sys.stdout.flush()
                idx += 1
                time.sleep(0.1)
        spinner_thread = threading.Thread(target=spinner_task)
        spinner_thread.start()
        raw_logs, current_phase = [], 0
        for line in process.stdout:
            raw_logs.append(line)
            keys_to_remove = []
            for key, description in phases.items():
                if key in line:
                    current_phase += 1
                    ui_state['desc'] = description
                    ui_state['percent'] = int((current_phase / total_phases) * 100)
                    ui_state['bar'] = f"[{'#' * current_phase}{'.' * (total_phases - current_phase)}]"
                    keys_to_remove.append(key)
            for k in keys_to_remove: del phases[k]
        process.wait()
        ui_state['is_running'] = False
        spinner_thread.join()
        sys.stdout.write(f"\r[{'#' * total_phases}] 100% | Build complete!\n")
        sys.stdout.flush()
        if process.returncode != 0:
            print("\nBUILD FAILED! Last logs:")
            for line in raw_logs[-30:]:
                print(line, end='')
            with open('build_version.txt', 'w') as f: f.write(str(version))
            return
    except Exception as e:
        print(f"\nBuild error: {e}")
        return

    dist_main_dir = os.path.join(current_dir, 'dist', app_name)
    for folder in ['ProcessedData', 'SpectralData', 'SpectralBinData', 'TimeDomainData']:
        os.makedirs(os.path.join(dist_main_dir, folder), exist_ok=True)

    # Копируем конфиги в папку с программой (на случай если add-data положил их в _internal)
    config_files = ['config_interrogator.json', 'plotting_parameters.txt',
                    'ZeroPosition.txt', 'PiezoStageStartPosition.json']
    for fname in config_files:
        src = os.path.join(current_dir, fname)
        dst = os.path.join(dist_main_dir, fname)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            print(f" -> Скопирован {fname}")

    # Копируем vendor-пакеты (pyvisa, pipython и т.д.) в _internal
    # (PyInstaller 6.20 на Python 3.14 не пакует их в PYZ из-за бага)
    vendor_src = os.path.join(current_dir, 'vendor_pkgs')
    vendor_dst = os.path.join(dist_main_dir, '_internal')
    if os.path.exists(vendor_src):
        for item in os.listdir(vendor_src):
            s = os.path.join(vendor_src, item)
            d = os.path.join(vendor_dst, item)
            if os.path.isdir(s) and not os.path.exists(d) and item != '__pycache__':
                shutil.copytree(s, d, ignore=shutil.ignore_patterns('__pycache__'))
                print(f" -> Vendor-пакет скопирован: {item}")
            elif os.path.isfile(s) and not os.path.exists(d) and item.endswith('.py'):
                shutil.copy2(s, d)
                print(f" -> Vendor-файл скопирован: {item}")

    # === ВАЛИДАЦИЯ ===
    exe_path = os.path.join(dist_main_dir, f"{app_name}.exe")
    if os.path.exists(exe_path):
        exe_size_mb = os.path.getsize(exe_path) / 1024 / 1024
        print(f"\n[OK] EXE файл найден: {exe_size_mb:.2f} MB")
    else:
        print("\n[FAIL] EXE файл не создан!")
        sys.exit(1)

    # Копируем .pkl3d файлы из ProcessedData/ в сборку
    processed_src = os.path.join(current_dir, 'ProcessedData')
    processed_dst = os.path.join(dist_main_dir, 'ProcessedData')
    if os.path.exists(processed_src):
        for item in os.listdir(processed_src):
            s = os.path.join(processed_src, item)
            d = os.path.join(processed_dst, item)
            if os.path.isfile(s) and not os.path.exists(d) and item.endswith(('.pkl3d', '.pkl')):
                shutil.copy2(s, d)
                print(f" -> Данные скопированы: {item}")

    # === СОЗДАНИЕ АРХИВА ===
    print("\n=== СОЗДАНИЕ АРХИВА ===")
    import zipfile
    zip_name = os.path.join(current_dir, 'dist', f"{app_name}.zip")
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_main_dir):
            # Сохраняем все папки (включая пустые)
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                arcname = os.path.relpath(dir_path, os.path.join(dist_main_dir, '..'))
                zipf.write(dir_path, arcname)
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.join(dist_main_dir, '..'))
                zipf.write(file_path, arcname)
    print(f"[OK] Архив создан: {zip_name}")
    zip_size_mb = os.path.getsize(zip_name) / 1024 / 1024
    print(f"     Размер: {zip_size_mb:.2f} MB")

    print(f"\n=== СБОРКА УСПЕШНО ЗАВЕРШЕНА! ===\nГотовая программа: {dist_main_dir}")

if __name__ == "__main__":
    main()