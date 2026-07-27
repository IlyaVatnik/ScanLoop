import clr, time, sys, inspect
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
dll_path = r'C:\Program Files\Thorlabs\Kinesis'
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

# Check LoadMotorConfiguration overloads via reflection
import System.Reflection

ch_type = None
for asm in System.AppDomain.CurrentDomain.GetAssemblies():
    for t in asm.GetTypes():
        if t.Name == 'StepperMotorChannel':
            ch_type = t
            break

if ch_type:
    method = ch_type.GetMethod('LoadMotorConfiguration', System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance)
    if method:
        print(f'LoadMotorConfiguration:')
        for overload in method.GetOverloads() if hasattr(method, 'GetOverloads') else [method]:
            pars = overload.GetParameters()
            for p in pars:
                print(f'  {p.Name}: {p.ParameterType}')
            print()

DeviceManagerCLI.Initialize()
time.sleep(2)
DeviceManagerCLI.BuildDeviceList()
time.sleep(3)
serial = '70864299'
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
device.Connect(serial)
time.sleep(5)

ch1 = device.GetChannel(1)

# Try LoadMotorConfiguration with different overloads
# The error was NullReferenceException in GetCurrentDeviceSettings
# Maybe we need to provide the stage type name explicitly

# Try: LoadMotorConfiguration(serial, stageType)
print('\nTrying LoadMotorConfiguration(serial, stageType)...')
for stage in ['NRT100', 'HS NRT100/M', 'NRT100/M', 'BSC202', '']:
    try:
        ch1.LoadMotorConfiguration(serial, stage)
        time.sleep(3)
        pp = ch1.GetPowerParams()
        print(f'  stage={stage}: SUCCESS! rest={pp.restPercentage}, move={pp.movePercentage}')
        break
    except Exception as e:
        err_str = str(e)[:80]
        print(f'  stage={stage}: {err_str}')

# If that didn't work, try using GetSettings
print('\nTrying GetSettings...')
try:
    settings = ch1.GetSettings()
    print(f'  Settings: {settings}')
except Exception as e:
    print(f'  Error: {str(e)[:80]}')

# Try MotorDeviceSettings
print('\nTrying MotorDeviceSettings...')
try:
    ms = ch1.MotorDeviceSettings
    print(f'  MotorDeviceSettings: {ms}')
except Exception as e:
    print(f'  Error: {str(e)[:80]}')
