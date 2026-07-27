import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

dll_path = r'C:\Program Files\Thorlabs\Kinesis'
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.GenericMotorCLI.dll')

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

print('Init...')
DeviceManagerCLI.Initialize()
time.sleep(2)
DeviceManagerCLI.BuildDeviceList()
time.sleep(3)

serial = '70864299'
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
time.sleep(1)

# Try Connect with overloads
print(f'\nConnect overloads:')
for o in device.Connect.Overloads:
    print(f'  {o}')

# Try (serial, timeout)
print('\nTrying Connect(serial, 5000)...')
try:
    device.Connect(serial, 5000)
    time.sleep(5)
except Exception as e:
    print(f'Error: {e}')

print(f'IsConnected={device.IsConnected}, IsSimulation={device.IsSimulation}')

if not device.IsConnected:
    # Try RegisterDevice then Connect
    print('\nTrying RegisterDevice...')
    try:
        DeviceManagerCLI.RegisterDevice(serial)
        time.sleep(2)
        device2 = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
        device2.Connect(serial, 5000)
        time.sleep(5)
        print(f'IsConnected={device2.IsConnected}')
    except Exception as e:
        print(f'Error: {e}')

# Check channel
try:
    ch = device.GetChannel(1)
    print(f'\nChannel 1 type: {type(ch)}')
    ch_methods = [m for m in dir(ch) if 'ower' in m or 'aram' in m or 'oad' in m]
    print(f'  Methods: {ch_methods}')
    
    # Try GetPowerParams on channel
    pp = ch.GetPowerParams()
    print(f'  PowerParams: rest={pp.restPercentage}, move={pp.movePercentage}')
except Exception as e:
    print(f'Channel error: {e}')
