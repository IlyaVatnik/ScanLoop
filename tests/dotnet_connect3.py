"""Try .NET API with the pattern that worked before (IsConnected=True)."""
import os
import sys
import clr
import time

KINESIS = r"C:\Program Files\Thorlabs\Kinesis"
os.add_dll_directory(KINESIS)
os.environ["PATH"] = KINESIS + ";" + os.environ.get("PATH", "")

for dll in [
    "Thorlabs.MotionControl.DeviceManagerCLI.dll",
    "Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll",
]:
    clr.AddReference(os.path.join(KINESIS, dll))

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

# 1. Build device list
DeviceManagerCLI.BuildDeviceList()

# 2. Create + Connect the way it worked before
dev = BenchtopStepperMotor.CreateBenchtopStepperMotor("70864299")
print(f"Created, IsConnected before connect: {dev.IsConnected}")

try:
    dev.Connect("70864299")
    print(f"Connect OK, IsConnected: {dev.IsConnected}")
except Exception as e:
    print(f"Connect exception: {e}")
    # Try alternate: maybe use serial with channel suffix?
    try:
        dev2 = BenchtopStepperMotor.CreateBenchtopStepperMotor("70864299-1")
        dev2.Connect("70864299-1")
        print(f"Connect with -1 OK: {dev2.IsConnected}")
    except Exception as e2:
        print(f"Connect -1 error: {e2}")

# 3. If connected, check settings state
print(f"\nIsSettingsInitialized: {dev.IsSettingsInitialized}")

# 4. Try LoadMotorConfiguration with different options
print("\n--- Try LoadMotorConfiguration ---")
try:
    dev.LoadMotorConfiguration("70864299")
    print("LoadMotorConfiguration OK!")
except Exception as e:
    print(f"LoadMotorConfiguration error: {type(e).__name__}: {e}")

# 5. Try StartPolling from the channel
print("\n--- Channel access ---")
try:
    ch = dev.GetChannel(1)
    print(f"Channel 1: {ch}")
    ch.StartPolling(250)
    print("StartPolling on channel OK")
    time.sleep(0.5)
    print(f"Position: {ch.Position}")
    print(f"IsEnabled: {ch.IsEnabled}")
except Exception as e:
    print(f"Channel error: {e}")

# 6. Try StopImmediate (worked before)
print("\n--- Try StopImmediate ---")
try:
    dev.StopImmediate()
    print("StopImmediate OK")
except Exception as e:
    print(f"StopImmediate error: {e}")
