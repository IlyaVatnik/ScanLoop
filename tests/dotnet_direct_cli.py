"""Try .NET API without LoadMotorConfiguration - use CLI DLL directly."""
import os
import sys
import clr

KINESIS = r"C:\Program Files\Thorlabs\Kinesis"
os.add_dll_directory(KINESIS)
os.environ["PATH"] = KINESIS + ";" + os.environ.get("PATH", "")

# Load core assemblies
for dll in [
    "Thorlabs.MotionControl.DeviceManagerCLI.dll",
    "Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll",
]:
    path = os.path.join(KINESIS, dll)
    clr.AddReference(path)
    print(f"Loaded: {dll}")

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

# 1. Build device list
result = DeviceManagerCLI.BuildDeviceList()
print(f"BuildDeviceList: {result}")

# 2. Try creating device directly without serial (generic)
print("\n--- Try creating device with serial ---")
try:
    dev = BenchtopStepperMotor.CreateBenchtopStepperMotor("70864299")
    print(f"Device created: {dev}")
    print(f"Device type: {type(dev)}")
except Exception as e:
    print(f"CreateBenchtopStepperMotor error: {e}")

# 3. Try Connect
print("\n--- Try Connect ---")
try:
    dev2 = BenchtopStepperMotor.CreateBenchtopStepperMotor("70864299")
    dev2.Connect("70864299")
    print(f"IsConnected: {dev2.IsConnected}")
    print(f"IsSettingsInitialized: {dev2.IsSettingsInitialized}")
except Exception as e:
    print(f"Connect error: {e}")

# 4. Try StartPolling
print("\n--- Try StartPolling ---")
try:
    dev2.StartPolling(250)
    print(f"IsEnabled: {dev2.IsEnabled}")
    import time
    time.sleep(1)
    state = dev2.State
    print(f"State: {state}")
except Exception as e:
    print(f"Polling error: {e}")

# 5. Try to access channel directly without settings
print("\n--- Try channel access ---")
try:
    ch = dev2.GetChannel(1)
    print(f"Channel 1: {ch}")
    print(f"Channel type: {type(ch)}")
    # Try to get position
    pos = ch.Position
    print(f"Position: {pos}")
except Exception as e:
    print(f"Channel error: {e}")

# 6. Try EnableDevice
print("\n--- Try EnableDevice ---")
try:
    dev2.EnableDevice()
    print("Device enabled")
except Exception as e:
    print(f"EnableDevice error: {e}")

# 7. Try homing
print("\n--- Try Home ---")
try:
    ch.Home()
    print("Home command sent")
except Exception as e:
    print(f"Home error: {e}")

# 8. Try Stop
print("\n--- Try Stop ---")
try:
    ch.Stop()
    print("Stop sent")
except Exception as e:
    print(f"Stop error: {e}")
