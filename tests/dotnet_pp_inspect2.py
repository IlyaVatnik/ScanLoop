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

for asm in System.AppDomain.CurrentDomain.GetAssemblies():
    for t in asm.GetTypes():
        if 'PowerParameter' in t.Name:
            print(f'\n=== {t.FullName} (asm: {asm.GetName().Name}) ===')
            print(f'  IsPublic: {t.IsPublic}')
            print(f'  IsValueType: {t.IsValueType}')
            print(f'  BaseType: {t.BaseType}')
            for f in t.GetFields(System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Static):
                print(f'  Field: {f.Name} ({f.FieldType}) public={f.IsPublic}')
            for p in t.GetProperties(System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance):
                print(f'  Property: {p.Name} ({p.PropertyType})')
            for c in t.GetConstructors(System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance):
                pars = [str(pt) for pt in c.GetParameters()]
                print(f'  Constructor: ({", ".join(pars)})')
