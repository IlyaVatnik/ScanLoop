import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

dll_path = r'C:\Program Files\Thorlabs\Kinesis'

clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

print('Loading assemblies...')
DeviceManagerCLI.Initialize()
time.sleep(3)

# Try scanning
print('Scanning for devices...')
try:
    DeviceManagerCLI.ScanForDevices()
    time.sleep(5)
except Exception as e:
    print(f'Scan error: {e}')

devices = DeviceManagerCLI.GetDeviceList()
print(f'Devices found: {list(devices)}')

# Also check DeviceManagerCLI methods
methods = [m for m in dir(DeviceManagerCLI) if not m.startswith('_')]
print(f'\nDeviceManagerCLI methods: {methods}')
