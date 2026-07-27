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

for ch_num in [1, 2]:
    ch = device.GetChannel(ch_num)
    print(f'\n=== Channel {ch_num} ===')
    
    try:
        pos = ch.Position
        print(f'  Position: {pos}')
    except Exception as e:
        print(f'  Position error: {str(e)[:80]}')
    
    try:
        bits = ch.GetStatusBits()
        print(f'  Status: 0x{bits:08X}')
    except Exception as e:
        print(f'  Status error: {str(e)[:80]}')

    try:
        ch.StopImmediate()
        print(f'  StopImmediate: OK')
        time.sleep(0.5)
    except Exception as e:
        print(f'  StopImmediate error: {str(e)[:80]}')
    
    try:
        ch.SetPositionCounter(0)
        print(f'  SetPositionCounter(0): OK')
    except Exception as e:
        print(f'  SetPositionCounter error: {str(e)[:80]}')

# Now try to move ch2 +40um (raw steps: 40um / 0.002mm = 20 steps)
print('\n=== Moving ch2 +40um (20 raw steps) ===')
ch2 = device.GetChannel(2)
try:
    ch2.MoveRelative(20)
    print('  MoveRelative(20): started')
    time.sleep(3)
    pos = ch2.Position
    print(f'  Final position: {pos}')
    bits = ch2.GetStatusBits()
    print(f'  Status: 0x{bits:08X}')
except Exception as e:
    print(f'  Error: {e}')

# Now try ch1
print('\n=== Moving ch1 +40um (20 raw steps) ===')
ch1 = device.GetChannel(1)
try:
    ch1.MoveRelative(20)
    print('  MoveRelative(20): started')
    time.sleep(3)
    pos = ch1.Position
    print(f'  Final position: {pos}')
    bits = ch1.GetStatusBits()
    print(f'  Status: 0x{bits:08X}')
except Exception as e:
    print(f'  Error: {e}')

device.Disconnect()
