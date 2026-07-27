import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
dll_path = r'C:\Program Files\Thorlabs\Kinesis'
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceConfiguration
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

DeviceSettingsUseOptionType = DeviceConfiguration.DeviceSettingsUseOptionType

print('Enum values:')
for name in dir(DeviceSettingsUseOptionType):
    if not name.startswith('_'):
        try:
            val = getattr(DeviceSettingsUseOptionType, name)
            print(f'  {name} = {int(val)}')
        except:
            pass

DeviceManagerCLI.Initialize()
time.sleep(2)
DeviceManagerCLI.BuildDeviceList()
time.sleep(3)
serial = '70864299'
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
device.Connect(serial)
time.sleep(5)

for ch_num in [1, 2]:
    ch = device.GetChannel(ch_num)
    
    for opt_name in ['UseDeviceSettings', 'UseFileSettings', 'UseConfiguredSettings']:
        try:
            enum_val = getattr(DeviceSettingsUseOptionType, opt_name)
            print(f'\nCh{ch_num}: LoadMotorConfiguration(serial, {opt_name})...')
            ch.LoadMotorConfiguration(serial, enum_val)
            time.sleep(3)
            pp = ch.GetPowerParams()
            print(f'  SUCCESS! rest={pp.restPercentage}, move={pp.movePercentage}')
            break
        except Exception as e:
            err = str(e)[:120]
            print(f'  {opt_name}: {err}')
    else:
        print(f'  All options failed for ch{ch_num}')
