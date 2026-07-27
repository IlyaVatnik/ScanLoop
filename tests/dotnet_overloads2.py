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

ch1 = device.GetChannel(1)

# Check LoadMotorConfiguration overloads via Overloads
print('LoadMotorConfiguration overloads:')
lmoc = ch1.LoadMotorConfiguration
print(type(lmoc))

# Try using reflection on the runtime type
rt = System.Object.GetType(ch1)
for m in rt.GetMethods():
    if m.Name == 'LoadMotorConfiguration':
        pars = m.GetParameters()
        par_str = ', '.join([f'{p.Name}: {p.ParameterType.Name}' for p in pars])
        print(f'  ({par_str})')

# Try the enum
print('\nSearching for settings option types...')
for asm in System.AppDomain.CurrentDomain.GetAssemblies():
    for t in asm.GetTypes():
        if t.IsEnum and ('Setting' in t.Name or 'Option' in t.Name):
            if 'Device' in t.Name or 'Motor' in t.Name:
                vals = [v.Name for v in t.GetFields() if v.IsLiteral]
                if vals:
                    print(f'  {t.Name}: {vals}')
