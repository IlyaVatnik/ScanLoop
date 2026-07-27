import subprocess, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Close TestClient
subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.TestClient.exe'], capture_output=True)
time.sleep(5)

# Now verify via .NET API
import clr
dll_path = r'C:\Program Files\Thorlabs\Kinesis'
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.DeviceManagerCLI.dll')
clr.AddReference(dll_path + r'\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll')
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor

DeviceManagerCLI.Initialize()
time.sleep(2)
DeviceManagerCLI.BuildDeviceList()
time.sleep(3)

serial = '70864299'
device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial)
device.Connect(serial)
time.sleep(5)

print(f'Connected: {device.IsConnected}')

# Check if settings initialized
for ch_num in [1, 2]:
    ch = device.GetChannel(ch_num)
    try:
        ch.RequestPowerParams()
        time.sleep(0.5)
        pp = ch.GetPowerParams()
        print(f'Ch{ch_num}: rest={pp.restPercentage}, move={pp.movePercentage}')
    except Exception as e:
        print(f'Ch{ch_num}: {e}')

device.Disconnect()
