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

pp_type = None
for asm in System.AppDomain.CurrentDomain.GetAssemblies():
    for t in asm.GetTypes():
        if t.Name == 'MOT_PowerParameters':
            pp_type = t
            print(f'Found: {t.FullName} in {asm.GetName().Name}')
            for f in t.GetFields():
                print(f'  Field: {f.Name} ({f.FieldType})')
            for p in t.GetProperties():
                print(f'  Property: {p.Name} ({p.PropertyType})')
            for c in t.GetConstructors():
                pars = [str(pt) for pt in c.GetParameters()]
                print(f'  Constructor: ({", ".join(pars)})')
            break
