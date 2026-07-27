import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

dll_path = r'C:\Program Files\Thorlabs\Kinesis'

# Load assemblies
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

print('Assemblies loaded')

# Initialize DeviceManager
DeviceManagerCLI.Initialize()
time.sleep(2)

print(f'Devices: {DeviceManagerCLI.GetDeviceList()}')

# Get device
serial = '70864299'
try:
    device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
    print(f'Device created: {device}')
    time.sleep(3)
    
    # Initialize settings
    settings = device.GetMetaData(serial)
    print(f'Settings: {settings}')
    
except Exception as e:
    print(f'Error: {e}')
