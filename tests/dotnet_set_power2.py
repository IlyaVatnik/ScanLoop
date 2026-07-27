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

# Create PowerParameters with rest=6, move=6
pp_class = None
for asm in System.AppDomain.CurrentDomain.GetAssemblies():
    for t in asm.GetTypes():
        if t.Name == 'PowerParameters' and 'ControlParameters' in t.FullName:
            pp_class = t
            break

print(f'PowerParameters class: {pp_class}')

# Create with default constructor
pp_obj = System.Activator.CreateInstance(pp_class)
print(f'Default: rest={pp_obj.RestPercentage}, move={pp_obj.MovePercentage}')

pp_obj.RestPercentage = 6
pp_obj.MovePercentage = 6
print(f'Set: rest={pp_obj.RestPercentage}, move={pp_obj.MovePercentage}')

# Now try SetPowerParams with this object
ch1 = device.GetChannel(1)
try:
    result = ch1.SetPowerParams(pp_obj)
    print(f'Ch1 SetPowerParams(PowerParameters): {result}')
except Exception as e:
    print(f'Ch1 SetPowerParams(PowerParameters) error: {e}')
    
    # Try converting to MOT_PowerParameters
    print('\nTrying MOT_PowerParameters via CreateInstance...')
    mot_pp_type = None
    for asm in System.AppDomain.CurrentDomain.GetAssemblies():
        for t in asm.GetTypes():
            if t.Name == 'MOT_PowerParameters' and t.IsValueType:
                mot_pp_type = t
                break
    
    mot_pp = System.Activator.CreateInstance(mot_pp_type)
    print(f'MOT_PowerParameters created: {mot_pp}')
    print(f'  type: {type(mot_pp)}')
    print(f'  fields: {[f.Name for f in mot_pp_type.GetFields()]}')
    
    # Try setting via the PowerParameters constructor overload
    try:
        ctor = mot_pp_type.GetConstructor([pp_class])
        if ctor:
            mot_pp2 = ctor.Invoke([pp_obj])
            print(f'Created from PowerParameters: {mot_pp2}')
    except Exception as e2:
        print(f'Constructor error: {e2}')
