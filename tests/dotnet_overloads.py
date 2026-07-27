import clr, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
dll_path = r'C:\Program Files\Thorlabs\Kinesis'
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor
import System.Reflection

DeviceManagerCLI.Initialize()
time.sleep(2)
DeviceManagerCLI.BuildDeviceList()
time.sleep(3)
serial = '70864299'
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
device.Connect(serial)
time.sleep(5)

ch1 = device.GetChannel(1)

# List all LoadMotorConfiguration overloads
ch_type = type(ch1)
for m in ch_type.GetMethods():
    if m.Name == 'LoadMotorConfiguration':
        pars = m.GetParameters()
        par_str = ', '.join([f'{p.Name}: {p.ParameterType.Name}' for p in pars])
        print(f'  LoadMotorConfiguration({par_str})')

# Try each overload
print('\nOverload 1: (serial)')
try:
    ch1.LoadMotorConfiguration(serial)
    time.sleep(5)
    pp = ch1.GetPowerParams()
    print(f'  SUCCESS! rest={pp.restPercentage}, move={pp.movePercentage}')
except Exception as e:
    print(f'  Error: {str(e)[:120]}')

# Overload 2: (serial, stageName)  
print('\nOverload 2: (serial, "NRT100/M")')
try:
    ch1.LoadMotorConfiguration(serial, 'NRT100/M')
    time.sleep(5)
    pp = ch1.GetPowerParams()
    print(f'  SUCCESS! rest={pp.restPercentage}, move={pp.movePercentage}')
except Exception as e:
    print(f'  Error: {str(e)[:120]}')

# Overload 3: (serial, useOptionType) - maybe need DeviceSettingsUseOptionType enum
print('\nLooking for DeviceSettingsUseOptionType...')
for asm in System.AppDomain.CurrentDomain.GetAssemblies():
    for t in asm.GetTypes():
        if 'SettingsUseOption' in t.Name or 'DeviceSettings' in t.Name:
            if t.IsEnum:
                print(f'  Enum: {t.FullName}')
                for v in t.GetFields():
                    if v.IsLiteral:
                        print(f'    {v.Name} = {v.GetRawConstantValue()}')
