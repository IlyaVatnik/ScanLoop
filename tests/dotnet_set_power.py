import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
dll_path = r'C:\Program Files\Thorlabs\Kinesis'
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor
import System

DeviceManagerCLI.Initialize()
time.sleep(2)
DeviceManagerCLI.BuildDeviceList()
time.sleep(3)

serial = '70864299'
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
device.Connect(serial)
time.sleep(5)
print(f'Connected: {device.IsConnected}')

pp_type = None
for asm in System.AppDomain.CurrentDomain.GetAssemblies():
    for t in asm.GetTypes():
        if t.Name == 'MOT_PowerParameters' and 'GenericMotor.' in t.FullName:
            pp_type = t
            break

pp_obj = System.Activator.CreateInstance(pp_type)

rest_field = pp_type.GetField('restPercentage')
move_field = pp_type.GetField('movePercentage')
rest_field.SetValue(pp_obj, 6)
move_field.SetValue(pp_obj, 6)
print(f'PowerParams created: rest={rest_field.GetValue(pp_obj)}, move={move_field.GetValue(pp_obj)}')

for ch_num in [1, 2]:
    ch = device.GetChannel(ch_num)
    try:
        result = ch.SetPowerParams(pp_obj)
        print(f'Ch{ch_num} SetPowerParams: result={result}')
        time.sleep(1)
        
        ch.RequestPowerParams()
        time.sleep(0.5)
        
        pp_read = ch.GetPowerParams()
        print(f'Ch{ch_num} ReadBack: rest={pp_read.restPercentage}, move={pp_read.movePercentage}')
    except Exception as e:
        print(f'Ch{ch_num} error: {e}')

# Persist
for ch_num in [1, 2]:
    ch = device.GetChannel(ch_num)
    try:
        ch.PersistSettings()
        print(f'Ch{ch_num} PersistSettings: OK')
        time.sleep(2)
    except Exception as e:
        print(f'Ch{ch_num} PersistSettings error: {e}')

# Final readback
print('\n=== Final Readback ===')
for ch_num in [1, 2]:
    ch = device.GetChannel(ch_num)
    try:
        ch.RequestPowerParams()
        time.sleep(0.5)
        pp = ch.GetPowerParams()
        print(f'Ch{ch_num}: rest={pp.restPercentage}, move={pp.movePercentage}')
    except Exception as e:
        print(f'Ch{ch_num}: {e}')

device.Disconnect()
print('\nDone!')
