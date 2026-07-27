import ctypes, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class MOT_PowerParameters(ctypes.Structure):
    _fields_ = [("restPercentage", ctypes.c_ushort),
                ("movePercentage", ctypes.c_ushort)]

dll = ctypes.CDLL('C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.Benchtop.StepperMotor.dll')

serial = b'70864299'

# Try all serial formats
for s in [b'70864299', b'70864299-1', b'70864299-2', b'70864299-3']:
    err = dll.SBC_Open(s)
    print(f'SBC_Open({s}): {err}')
    if err == 0:
        dll.SBC_Close(s)
        break
    time.sleep(0.5)

# If all fail, try after TLI_BuildDeviceList
print('\nTrying TLI_BuildDeviceList first...')
tlilite = ctypes.CDLL('C:/Program Files/Thorlabs/Thorlabs.MotionControl.TLILite.TLI.dll')
err = tlilite.TLI_BuildDeviceList()
print(f'TLI_BuildDeviceList: {err}')
time.sleep(2)

size = tlilite.TLI_GetDeviceListSize()
print(f'Device list size: {size}')

for s in [b'70864299']:
    err = dll.SBC_Open(s)
    print(f'SBC_Open({s}): {err}')
    if err == 0:
        for ch in [1, 2]:
            dll.SBC_StartPolling(s, ch, 250)
            time.sleep(0.5)
            pp = MOT_PowerParameters()
            dll.SBC_RequestPowerParams(s, ch)
            time.sleep(0.3)
            err2 = dll.SBC_GetPowerParams(s, ch, ctypes.byref(pp))
            print(f'  Ch{ch}: err={err2}, rest={pp.restPercentage}, move={pp.movePercentage}')
            dll.SBC_StopPolling(s, ch)
        dll.SBC_Close(s)
