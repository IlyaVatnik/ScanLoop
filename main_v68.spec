# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['Scripts.ScanningProcessOSA', 'Scripts.ScanningProcessLaser', 'Scripts.ScanningProcessScope', 'Scripts.Analyzer', 'Scripts.Spectral_processor', 'Scripts.SNAP_experiment', 'Scripts.OVA_signals', 'Scripts.TD_processor', 'Scripts.analyze_oscillogram', 'Hardware.Stages.stages_manager', 'Hardware.Stages.PIStages', 'Hardware.Stages.PiezoStageE53D_serial', 'Hardware.Scanner', 'Hardware.Config', 'serial.tools.list_ports', 'pipython', 'matplotlib.backends.backend_qt5agg', 'matplotlib.backends.backend_qt5', 'pyvisa', 'pyvisa_py', 'pyusb', 'typing_extensions']
hiddenimports += collect_submodules('Common')
hiddenimports += collect_submodules('Windows_GUI')
hiddenimports += collect_submodules('Hardware')
hiddenimports += collect_submodules('Scripts')
hiddenimports += collect_submodules('Utils')
hiddenimports += collect_submodules('Logger')
hiddenimports += collect_submodules('Visualization')
hiddenimports += collect_submodules('Theory')
hiddenimports += collect_submodules('Hardware.Stages')
hiddenimports += collect_submodules('Hardware.Stages.Standa')
hiddenimports += collect_submodules('Hardware.Stages.LBTEK')
hiddenimports += collect_submodules('Hardware.PyApex')
hiddenimports += collect_submodules('Hardware.LaserLibs')
hiddenimports += collect_submodules('Windows_GUI.UIs')


a = Analysis(
    ['main.py'],
    pathex=['.', 'Hardware\\Stages', 'vendor_pkgs'],
    binaries=[('C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.KCube.DCServo.dll', '.'), ('C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.Benchtop.StepperMotor.dll', '.'), ('C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManager.dll', '.'), ('C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.PrivateInternal.dll', '.'), ('C:\\Program Files\\Thorlabs\\Kinesis\\ftd2xx.dll', '.'), ('C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.FTD2xx_Net.dll', '.')],
    datas=[('Hardware\\Stages\\Standa', 'Hardware/Stages/Standa'), ('Hardware\\Stages\\LBTEK\\LBTEKx64', 'Hardware/Stages/LBTEK/LBTEKx64'), ('config_interrogator.json', '.'), ('plotting_parameters.txt', '.'), ('ZeroPosition.txt', '.'), ('PiezoStageStartPosition.json', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6', 'PySide6'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main_v68',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main_v68',
)
