import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
dll_path = r'C:\Program Files\Thorlabs\Kinesis'
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

DeviceManagerCLI.Initialize()
time.sleep(2)
DeviceManagerCLI.BuildDeviceList()
time.sleep(3)

serial = '70864299'
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
device.Connect(serial)
time.sleep(5)
print(f'Connected: {device.IsConnected}')

# Check IsBayValid for each channel
for ch_num in [1, 2, 3]:
    try:
        valid = device.IsBayValid(ch_num)
        print(f'Bay {ch_num} valid: {valid}')
    except Exception as e:
        print(f'Bay {ch_num}: {str(e)[:60]}')

# Try EnableDevice on ch2
ch2 = device.GetChannel(2)
print(f'\nCh2 IsEnabled: {ch2.IsEnabled}')

# Try enabling
try:
    ch2.EnableDevice()
    time.sleep(2)
    print(f'Ch2 After EnableDevice: IsEnabled={ch2.IsEnabled}')
except Exception as e:
    print(f'EnableDevice error: {e}')

# Try Enable with polling
try:
    ch2.StartPolling(250)
    time.sleep(1)
    print(f'Ch2 After StartPolling: IsEnabled={ch2.IsEnabled}')
except Exception as e:
    print(f'StartPolling error: {e}')

# Check state
try:
    state = ch2.State
    print(f'Ch2 State: {state}')
except Exception as e:
    print(f'State error: {str(e)[:80]}')

# Try move after enable
try:
    ch2.MoveRelative(20)
    print('Ch2 MoveRelative(20): started!')
    time.sleep(5)
except Exception as e:
    print(f'MoveRelative error: {str(e)[:80]}')

device.Disconnect()
