import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

dll_path = r'C:\Program Files\Thorlabs\Kinesis'

clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor
from Thorlabs.MotionControl.GenericMotorCLI import GenericMotorCLI

print('Loading assemblies...')
DeviceManagerCLI.Initialize()
time.sleep(2)

devices = DeviceManagerCLI.GetDeviceList()
print(f'Devices found: {list(devices)}')

serial = '70864299'
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
print(f'Device type: {type(device)}')
time.sleep(1)

# Show all methods containing "Power" or "Setting" or "Init"
methods = [m for m in dir(device) if 'ower' in m or 'etting' in m or 'nit' in m or 'ersist' in m or 'oad' in m]
print(f'\nRelevant methods: {methods}')

# Try to connect and load settings
try:
    print('\nConnecting...')
    device.Connect(serial)
    time.sleep(2)
    print('Connected!')
except Exception as e:
    print(f'Connect error: {e}')

# Try to get power params
try:
    print('\nTrying to load settings...')
    device.LoadSettings(serial)
    time.sleep(3)
    print('Settings loaded!')
except Exception as e:
    print(f'LoadSettings error: {e}')

# Try power params
for ch in [1, 2]:
    try:
        pp = device.GetPowerParams(ch)
        print(f'Ch{ch} PowerParams: {pp}')
        print(f'  rest={pp.restPercentage}, move={pp.movePercentage}')
    except Exception as e:
        print(f'Ch{ch} GetPowerParams error: {e}')
