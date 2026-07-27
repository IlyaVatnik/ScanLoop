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
device.Connect(serial)
time.sleep(5)
print(f'Connected: {device.IsConnected}')
print(f'Channels: {device.ChannelCount}')

# Get channel 1
ch1 = device.GetChannel(1)
print(f'\nChannel 1 type: {type(ch1)}')

# List all methods on channel
methods = [m for m in dir(ch1) if not m.startswith('_')]
print(f'\nChannel 1 methods ({len(methods)}):')
for m in sorted(methods):
    print(f'  {m}')

# Try GetPowerParams
print('\n--- Getting PowerParams ---')
for ch_num in [1, 2]:
    try:
        ch = device.GetChannel(ch_num)
        # Try various method names
        for method_name in ['GetPowerParams', 'RequestPowerParams']:
            if hasattr(ch, method_name):
                try:
                    result = getattr(ch, method_name)()
                    print(f'Ch{ch_num}.{method_name}() = {result}')
                    if hasattr(result, 'restPercentage'):
                        print(f'  rest={result.restPercentage}, move={result.movePercentage}')
                except Exception as e:
                    print(f'Ch{ch_num}.{method_name}() error: {e}')
    except Exception as e:
        print(f'Ch{ch_num} error: {e}')
