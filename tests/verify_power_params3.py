import ctypes, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class MOT_PowerParameters(ctypes.Structure):
    _fields_ = [("restPercentage", ctypes.c_ushort),
                ("movePercentage", ctypes.c_ushort)]

dll = ctypes.CDLL('C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.Benchtop.StepperMotor.dll')
serial = b'70864299'

err = dll.SBC_Open(serial)
print(f"Open: err={err}")
time.sleep(2)

for ch in [1, 2]:
    dll.SBC_StartPolling(serial, ch, 250)
    time.sleep(0.5)
    
    # Request first
    req_err = dll.SBC_RequestPowerParams(serial, ch)
    print(f"Channel {ch}: RequestPowerParams err={req_err}")
    time.sleep(0.3)
    
    pp = MOT_PowerParameters()
    err = dll.SBC_GetPowerParams(serial, ch, ctypes.byref(pp))
    print(f"Channel {ch}: GetPowerParams err={err}, rest={pp.restPercentage}, move={pp.movePercentage}")
    
    dll.SBC_StopPolling(serial, ch)
    time.sleep(0.2)

dll.SBC_Close(serial)
