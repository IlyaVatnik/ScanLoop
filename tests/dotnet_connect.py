import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

dll_path = r'C:\Program Files\Thorlabs\Kinesis'

clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.GenericMotorCLI.dll')

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

print('Init DeviceManager...')
DeviceManagerCLI.Initialize()
time.sleep(2)
DeviceManagerCLI.BuildDeviceList()
time.sleep(3)
print(f'Devices: {list(DeviceManagerCLI.GetDeviceList())}')

serial = '70864299'
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
time.sleep(1)

# Show available methods
all_methods = [m for m in dir(device) if not m.startswith('_')]
print(f'\nAll methods ({len(all_methods)}):')
for m in all_methods:
    print(f'  {m}')

# Try connecting via InitializeUSBConnectionState
print(f'\nTrying InitializeGenericDevice...')
try:
    device.InitializeGenericDevice(serial)
    time.sleep(3)
    print(f'Generic init done! IsSettingsKnown={device.IsSettingsKnown}')
except Exception as e:
    print(f'Error: {e}')
