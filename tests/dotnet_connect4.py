import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

dll_path = r'C:\Program Files\Thorlabs\Kinesis'
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.GenericMotorCLI.dll')

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotorChannel

print('Init...')
DeviceManagerCLI.Initialize()
time.sleep(2)
DeviceManagerCLI.BuildDeviceList()
time.sleep(3)

serial = '70864299'
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
time.sleep(1)

# Connect with timeout
print('\nTrying Connect with timeout...')
try:
    device.Connect(serial, 5000)
    time.sleep(5)
    print(f'IsConnected={device.IsConnected}')
except Exception as e:
    print(f'Error: {e}')

# If not connected, try direct USB 
if not device.IsConnected:
    print('\nTrying SetUSBConnectionState...')
    try:
        device.SetUSBConnectionState(serial, 5000, False)
        time.sleep(5)
        print(f'IsConnected={device.IsConnected}')
    except Exception as e:
        print(f'Error: {e}')

print(f'\nFinal state:')
print(f'  IsConnected={device.IsConnected}')
print(f'  IsSimulation={device.IsSimulation}')
print(f'  IsSettingsKnown={device.IsSettingsKnown}')
print(f'  ChannelCount={device.ChannelCount}')

# Try to access channel 0
try:
    ch = device.GetChannel(1)
    print(f'\nChannel 1: {ch}')
    ch_methods = [m for m in dir(ch) if 'ower' in m or 'aram' in m or 'etting' in m or 'oad' in m]
    print(f'  Relevant methods: {ch_methods}')
except Exception as e:
    print(f'GetChannel error: {e}')
