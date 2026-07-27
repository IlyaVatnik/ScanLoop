import ctypes, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

dll = ctypes.CDLL('C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.Benchtop.StepperMotor.dll')
serial = b'70864299'
dll.SBC_Open(serial)
time.sleep(1)

for ch in [1, 2]:
    dll.SBC_StartPolling(serial, ch, 250)
    time.sleep(0.5)
    
    rest = ctypes.c_uint32()
    move = ctypes.c_uint32()
    err = dll.SBC_GetPowerParams(serial, ch, ctypes.byref(rest), ctypes.byref(move))
    print(f"Channel {ch}: err={err}, restPercentage={rest.value}, movePercentage={move.value}")
    
    dll.SBC_StopPolling(serial, ch)
    time.sleep(0.2)

dll.SBC_Close(serial)
