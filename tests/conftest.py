import sys
from unittest.mock import MagicMock
from ctypes import c_short, c_int, c_ulong, c_ushort, byref


def _make_serial_buf_writer(value):
    val = value.encode("utf-8")
    def writer(buf, size):
        for i in range(len(val)):
            buf[i] = val[i]
        buf[len(val)] = 0
    return writer


def _val(obj):
    return obj.value if hasattr(obj, 'value') else obj


def _make_bsm_get_vel_params(initial_max=1000, initial_accel=250):
    """Возвращает side_effect для SBC_GetVelParams, который записывает
    текущие maxVel и accel в переданные указатели."""
    def getter(serial, channel, max_vel_ptr, accel_ptr):
        max_vel_ptr._obj.value = initial_max
        accel_ptr._obj.value = initial_accel
        return 0
    return getter


def _make_bsm_mock():
    m = MagicMock()
    m.DLL_AVAILABLE = True

    m.TLI_BuildDeviceList = MagicMock()
    m.TLI_GetDeviceListSize = MagicMock(return_value=1)
    m.TLI_GetDeviceListExt = MagicMock(side_effect=_make_serial_buf_writer("70864299"))
    m.SBC_Open = MagicMock(return_value=0)
    m.SBC_Close = MagicMock()
    m.SBC_GetNumChannels = MagicMock(return_value=c_short(3))
    m.SBC_IsChannelValid = MagicMock(return_value=True)
    m.SBC_LoadSettings = MagicMock(return_value=True)
    m.SBC_EnableChannel = MagicMock(return_value=0)
    m.SBC_SetBacklash = MagicMock()
    m.SBC_SetVelParams = MagicMock()
    m.SBC_GetVelParams = MagicMock(side_effect=_make_bsm_get_vel_params(1000, 250))
    m.SBC_GetDeviceUnitFromRealValue = MagicMock(return_value=0)
    m.SBC_StartPolling = MagicMock()
    m.SBC_StopPolling = MagicMock()
    m.SBC_ClearMessageQueue = MagicMock()
    m.SBC_SetMoveRelativeDistance = MagicMock()
    m.SBC_MoveRelativeDistance = MagicMock(return_value=0)
    m.SBC_GetPosition = MagicMock(return_value=c_int(0))
    m.SBC_RequestPosition = MagicMock(return_value=0)
    m.SBC_Home = MagicMock(return_value=0)
    m.SBC_NeedsHoming = MagicMock(return_value=True)
    m.SBC_CanHome = MagicMock(return_value=True)
    m.SBC_CanMoveWithoutHomingFirst = MagicMock(return_value=True)
    m.SBC_SetPositionCounter = MagicMock(return_value=0)
    m.SBC_RequestStatusBits = MagicMock(return_value=0)
    m.SBC_GetStatusBits = MagicMock(return_value=c_ulong(0))
    m.SBC_RequestPowerParams = MagicMock(return_value=0)
    m.SBC_GetPowerParams = MagicMock(return_value=0)
    m.SBC_RequestInputVoltage = MagicMock(return_value=0)
    m.SBC_GetInputVoltage = MagicMock(return_value=c_ushort(0))
    m.SBC_RequestHomingParams = MagicMock(return_value=0)
    m.SBC_GetHomingVelocity = MagicMock(return_value=500)
    m.SBC_SetHomingVelocity = MagicMock(return_value=0)
    m.MOT_PowerParameters = MagicMock()
    return m


def _make_kdc_mock():
    m = MagicMock()
    m.DLL_AVAILABLE = True
    m.TLI_BuildDeviceList = MagicMock()
    m.TLI_GetDeviceListSize = MagicMock(return_value=1)
    m.TLI_GetDeviceListExt = MagicMock(side_effect=_make_serial_buf_writer("70864299"))
    m.CC_Open = MagicMock(return_value=0)
    m.CC_Close = MagicMock()
    m.CC_SetVelParams = MagicMock()
    m.CC_StartPolling = MagicMock()
    m.CC_StopPolling = MagicMock()
    m.CC_ClearMessageQueue = MagicMock()
    m.CC_SetMoveRelativeDistance = MagicMock()
    m.CC_MoveRelativeDistance = MagicMock(return_value=0)
    m.CC_GetPosition = MagicMock(return_value=c_int(0))
    m.CC_Home = MagicMock(return_value=0)
    return m


_bsm = None
_kdc = None


def get_bsm_mock():
    global _bsm
    if _bsm is None:
        _bsm = _make_bsm_mock()
    return _bsm


def get_kdc_mock():
    global _kdc
    if _kdc is None:
        _kdc = _make_kdc_mock()
    return _kdc


kinesis_pkg = MagicMock()
kinesis_pkg.benchtop_stepper_motor = get_bsm_mock()
kinesis_pkg.KCube_DC_Servo = get_kdc_mock()

sys.modules["Hardware.Stages.thorlabs_kinesis"] = kinesis_pkg
sys.modules["Hardware.Stages.thorlabs_kinesis.benchtop_stepper_motor"] = get_bsm_mock()
sys.modules["Hardware.Stages.thorlabs_kinesis.KCube_DC_Servo"] = get_kdc_mock()
