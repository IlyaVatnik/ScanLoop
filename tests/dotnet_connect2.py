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

# Try ConnectDevice
print('\nTrying ConnectDevice...')
try:
    device.ConnectDevice(serial)
    time.sleep(5)
    print(f'Connected! IsConnected={device.IsConnected}')
    print(f'IsSettingsKnown={device.IsSettingsKnown}')
    print(f'IsSimulation={device.IsSimulation}')
    print(f'ChannelCount={device.ChannelCount}')
except Exception as e:
    print(f'ConnectDevice error: {e}')
    # Try other methods
    print('\nTrying InitializeUSBConnectionState...')
    try:
        device.InitializeUSBConnectionState(serial, False)
        time.sleep(5)
        print(f'Connected! IsConnected={device.IsConnected}')
        print(f'IsSettingsKnown={device.IsSettingsKnown}')
    except Exception as e2:
        print(f'Error: {e2}')
