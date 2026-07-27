import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
dll_path = r'C:\Program Files\Thorlabs\Kinesis'
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceSettingsUseOptionType
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

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
    
    # Try each DeviceSettingsUseOptionType
    for opt in ['UseDeviceSettings', 'UseFileSettings', 'UseConfiguredSettings']:
        try:
            enum_val = getattr(DeviceSettingsUseOptionType, opt)
            print(f'Ch{ch_num}: LoadMotorConfiguration({opt})...')
            ch.LoadMotorConfiguration(serial, enum_val)
            time.sleep(3)
            pp = ch.GetPowerParams()
            print(f'  SUCCESS! rest={pp.restPercentage}, move={pp.movePercentage}')
            break
        except Exception as e:
            err = str(e)[:80]
            print(f'  {opt}: {err}')
    else:
        print(f'  All options failed for ch{ch_num}')
