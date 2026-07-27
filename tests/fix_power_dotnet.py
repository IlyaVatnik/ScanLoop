"""
Fix PowerParams via .NET API — try GetMotorConfiguration to init settings.
"""
import sys, os, time

import clr
kinesis_dir = r"C:\Program Files\Thorlabs\Kinesis"
clr.AddReference(os.path.join(kinesis_dir, "Thorlabs.MotionControl.DeviceManagerCLI"))
clr.AddReference(os.path.join(kinesis_dir, "Thorlabs.MotionControl.Benchtop.StepperMotorCLI"))

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

SERIAL = "70864299"

DeviceManagerCLI.BuildDeviceList()
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(SERIAL)
device.Connect(SERIAL)
time.sleep(5)

for ch_num in range(1, 3):
    print(f"\n=== CHANNEL {ch_num} ===")
    ch = device.GetChannel(ch_num)
    
    # Try LoadMotorConfiguration with different overloads
    try:
        # Single-arg version
        config = ch.LoadMotorConfiguration(SERIAL)
        print(f"  LoadMotorConfiguration(serial): OK")
    except Exception as e:
        print(f"  LoadMotorConfiguration(serial): {str(e)[:100]}")
    
    # Try SetSettings with different args
    try:
        ms = ch.MotorDeviceSettings
        print(f"  MotorDeviceSettings: {ms}")
    except Exception as e:
        print(f"  MotorDeviceSettings: {str(e)[:100]}")
    
    try:
        ch.Wait(5000)
        print(f"  Wait OK")
    except Exception as e:
        print(f"  Wait: {str(e)[:100]}")

    # Try setting settings directly from file
    try:
        # Create settings from factory
        from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import ThorlabsBenchtopStepperMotorSettingsFactory
        factory = ThorlabsBenchtopStepperMotorSettingsFactory()
        settings = factory.CreateSettings(ch)
        print(f"  Factory settings: {type(settings)}")
    except Exception as e:
        print(f"  Factory: {str(e)[:100]}")

print("\n=== DONE ===")
