# Hardware/Stages/Thorlabs/thorlabs_stages.py
# -*- coding: utf-8 -*-
__version__ = '3.3'
__date__ = '2026.07.23'

# ===========================================================================
#  НАСТРОЙКИ СКОРОСТИ (менять здесь)
#  Для смены параметров измените значения ниже и пересоберите exe.
# ===========================================================================
DEFAULT_MAX_VELOCITY_MM_S = 2.0       # мм/с — максимальная скорость перемещения
DEFAULT_ACCELERATION_MM_S2 = 0.5      # мм/с² — ускорение
DEFAULT_HOMING_VELOCITY_MM_S = 5.0    # мм/с — скорость homing (поиска нуля)
# ===========================================================================

import os
import sys
import time
import logging
import decimal as _decimal
from ctypes import c_int, c_short, c_char_p, c_uint, c_long, c_double, byref

logger = logging.getLogger(__name__)

KINESIS_DIR = r"C:\Program Files\Thorlabs\Kinesis"


# ---------------------------------------------------------------------------
#  .NET API helpers (pythonnet required)
# ---------------------------------------------------------------------------
_dotnet_cache = {}


def _dotnet_init():
    """Import and initialize Thorlabs .NET API. Returns (DeviceManagerCLI, DeviceConfiguration, BenchtopStepperMotor, System)."""
    if 'modules' in _dotnet_cache:
        return _dotnet_cache['modules']

    try:
        import clr
    except ImportError:
        raise ImportError("pythonnet не установлен. pip install pythonnet")

    dlls = [
        'Thorlabs.MotionControl.DeviceManagerCLI.dll',
        'Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll',
        'Thorlabs.MotionControl.GenericMotorCLI.dll',
    ]
    for dll in dlls:
        clr.AddReference(os.path.join(KINESIS_DIR, dll))

    import System
    from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
    from Thorlabs.MotionControl.DeviceManagerCLI import DeviceConfiguration
    from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor
    _dotnet_cache['modules'] = (DeviceManagerCLI, DeviceConfiguration, BenchtopStepperMotor, System)
    return DeviceManagerCLI, DeviceConfiguration, BenchtopStepperMotor, System


def _dotnet_build(DeviceManagerCLI):
    """Initialize and build device list (safe to call multiple times)."""
    if _dotnet_cache.get('built'):
        return
    DeviceManagerCLI.Initialize()
    DeviceManagerCLI.BuildDeviceList()
    _dotnet_cache['built'] = True


# ---------------------------------------------------------------------------
#  C API helpers (for KDC and scanning only)
# ---------------------------------------------------------------------------
def _kinesis_paths():
    paths = [
        r"C:\Program Files\Thorlabs\Kinesis",
        r"C:\Program Files (x86)\Thorlabs\Kinesis",
    ]
    if getattr(sys, 'frozen', False):
        internal = os.path.join(os.path.dirname(sys.executable), '_internal')
        if os.path.isdir(internal):
            paths.append(internal)
    return paths


def _add_kinesis_to_path():
    if getattr(_add_kinesis_to_path, '_done', False):
        return
    _add_kinesis_to_path._done = True
    for p in _kinesis_paths():
        if os.path.isdir(p):
            try:
                os.add_dll_directory(p)
                logger.info(f"[Thorlabs] Добавлен путь к DLL: {p}")
            except AttributeError:
                logger.warning("[Thorlabs] os.add_dll_directory не поддерживается")


KDC_ENCODER_STEP = 0.03


def _scan_via(driver_module, label):
    """Возвращает список {'serial': ..., 'type': label}"""
    from ctypes import create_string_buffer

    dll_avail = getattr(driver_module, 'DLL_AVAILABLE', False)
    logger.info(f"[Thorlabs.{label}] DLL_AVAILABLE={dll_avail}")

    if not dll_avail:
        logger.warning(f"[Thorlabs.{label}] DLL недоступна — пропускаем")
        return []

    driver_module.TLI_BuildDeviceList()
    time.sleep(0.5)

    device_count = driver_module.TLI_GetDeviceListSize()
    logger.info(f"[Thorlabs.{label}] Найдено устройств: {device_count}")

    if device_count and device_count > 0:
        buf = create_string_buffer(1024)
        driver_module.TLI_GetDeviceListExt(buf, 1024)
        raw = buf.value.decode('utf-8')
        serials = [{'serial': s.strip(), 'type': label} for s in raw.split(',') if s.strip()]
        logger.info(f"[Thorlabs.{label}] Найдено: {serials}")
        return serials
    return []


def get_thorlabs_serials():
    """Сканирует устройства, добавляет каналы для BSM"""
    _add_kinesis_to_path()

    try:
        from Hardware.Stages.thorlabs_kinesis import benchtop_stepper_motor as bsm
        from Hardware.Stages.thorlabs_kinesis import KCube_DC_Servo as kdc
    except Exception as e:
        logger.warning(f"[Thorlabs] DLL не найдена: {e}")
        return []

    all_devices = []
    all_devices.extend(_scan_via(kdc, 'KDC'))
    all_devices.extend(_scan_via(bsm, 'BSM'))

    for dev in all_devices:
        if dev['type'] == 'BSM':
            ser = c_char_p(bytes(dev['serial'], "utf-8"))
            try:
                bsm.TLI_BuildDeviceList()
                bsm.SBC_Open(ser)
                time.sleep(0.1)
                n = bsm.SBC_GetNumChannels(ser)
                n_val = n.value if hasattr(n, 'value') else n
                dev['channels'] = [
                    ch for ch in range(1, n_val + 1)
                    if bsm.SBC_IsChannelValid(ser, c_short(ch))
                ]
                bsm.SBC_Close(ser)
                logger.info(f"[Thorlabs] BSM {dev['serial']}: каналы {dev['channels']}")
            except Exception as e:
                logger.warning(f"[Thorlabs] Не удалось получить каналы BSM {dev['serial']}: {e}")
                dev['channels'] = [0]

    return all_devices


class ThorlabsCube:
    def __init__(self, serial_no):
        _add_kinesis_to_path()

        try:
            from Hardware.Stages.thorlabs_kinesis import KCube_DC_Servo as kdc
        except FileNotFoundError as e:
            raise RuntimeError(f"Thorlabs DLL не найдена: {e}")

        self.serial_no = c_char_p(bytes(serial_no, "utf-8"))
        self.encoder_step = KDC_ENCODER_STEP
        self.milliseconds = c_int(100)
        self.is_connected = False
        self.kdc = kdc

        self.kdc.TLI_BuildDeviceList()
        err = self.kdc.CC_Open(self.serial_no)
        time.sleep(0.1)
        if err == 0:
            logger.info(f"[Thorlabs.KDC] Подключено: {serial_no}")
            kdc_min_vel = 5
            kdc_accel = int(10 / KDC_ENCODER_STEP)
            kdc_max_vel = int(2.0 / KDC_ENCODER_STEP)
            self.kdc.CC_SetVelParams(self.serial_no, c_int(kdc_min_vel), c_int(kdc_accel), c_int(kdc_max_vel))
            logger.info(f"[Thorlabs.KDC] Velocity set: minVel={kdc_min_vel}, accel={kdc_accel}, maxVel={kdc_max_vel}")
            self.is_connected = True
        else:
            raise RuntimeError(f"Не удалось подключиться к KDC {serial_no}")

    def get_position(self):
        raw = self.kdc.CC_GetPosition(self.serial_no)
        pos = raw.value if hasattr(raw, 'value') else int(raw)
        return round(pos, 1)

    def move_relative(self, distance_mkm):
        distance_mm = distance_mkm / 1000.0
        distance_in_steps = int(distance_mm / self.encoder_step)
        logger.info(f"[Thorlabs.KDC] move_relative: {distance_mkm} мкм = {distance_in_steps} шагов")
        self.kdc.CC_StartPolling(self.serial_no, self.milliseconds)
        self.kdc.CC_ClearMessageQueue(self.serial_no)
        time.sleep(0.1)
        self.kdc.CC_SetMoveRelativeDistance(self.serial_no, c_int(distance_in_steps))
        self.kdc.CC_MoveRelativeDistance(self.serial_no)
        time.sleep(0.5)
        self.kdc.CC_StopPolling(self.serial_no)

    def move_home(self):
        logger.info("[Thorlabs.KDC] move_home")
        self.kdc.CC_StartPolling(self.serial_no, self.milliseconds)
        self.kdc.CC_ClearMessageQueue(self.serial_no)
        self.kdc.CC_Home(self.serial_no)
        time.sleep(2)
        self.kdc.CC_StopPolling(self.serial_no)

    def wait_for_stop(self):
        pass

    def close(self):
        self.kdc.CC_Close(self.serial_no)
        logger.info(f"[Thorlabs.KDC] Закрыто: {self.serial_no.value.decode()}")

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class _BSMConnection:
    """Shared .NET connection to a Thorlabs BSM device (thread-safe singleton per serial)."""
    TIMEOUT = 30
    _instances = {}

    def __init__(self, serial_no):
        self.serial_no = serial_no
        self.refcount = 1
        self._closed = False

        DeviceManagerCLI, DeviceConfiguration, BenchtopStepperMotor, System = _dotnet_init()
        self._System = System
        self._DeviceManagerCLI = DeviceManagerCLI
        self._DeviceConfiguration = DeviceConfiguration

        _dotnet_build(DeviceManagerCLI)

        self.device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial_no)
        if self.device is None:
            raise RuntimeError(f"CreateBenchtopStepperMotor({serial_no}) вернул None")
        self.device.Connect(serial_no)
        time.sleep(1)

        if not self.device.IsConnected:
            raise RuntimeError(f"BSM {serial_no} не подключён")

        self._ch = {1: self.device.GetChannel(1), 2: self.device.GetChannel(2)}

        opt = DeviceConfiguration.DeviceSettingsUseOptionType.UseFileSettings
        for ch_num, ch_obj in self._ch.items():
            ch_obj.LoadMotorConfiguration(f'{serial_no}-{ch_num}', opt)
            time.sleep(0.5)
            valid = ch_obj.IsMotorSettingsValid
            logger.info(f"[Thorlabs.BSM] ch{ch_num} LoadMotorConfiguration: IsMotorSettingsValid={valid}")

        for ch_obj in self._ch.values():
            ch_obj.EnableDevice()
            time.sleep(0.2)
            ch_obj.StartPolling(250)
            time.sleep(0.2)

        for ch_num, ch_obj in self._ch.items():
            ch_obj.SetVelocityParams(
                self._System.Decimal(DEFAULT_MAX_VELOCITY_MM_S),
                self._System.Decimal(DEFAULT_ACCELERATION_MM_S2)
            )
            vp = ch_obj.GetVelocityParams()
            logger.info(f"[Thorlabs.BSM] ch{ch_num} Velocity set: "
                        f"maxVel={vp.MaxVelocity} mm/s, accel={vp.Acceleration} mm/s²")

        for ch_num, ch_obj in self._ch.items():
            pos = float(str(ch_obj.Position).replace(',', '.'))
            if pos < 0:
                try:
                    ch_obj.StopImmediate()
                except Exception:
                    pass
                time.sleep(0.1)
                ch_obj.SetPositionCounter(0)
                time.sleep(0.2)
                pos_after = float(str(ch_obj.Position).replace(',', '.'))
                logger.info(f"[Thorlabs.BSM] ch{ch_num} Position={pos} < 0 → reset SetPositionCounter(0), now={pos_after}")
                if pos_after < 0:
                    logger.warning(f"[Thorlabs.BSM] ch{ch_num} SetPositionCounter(0) did not reset position, "
                                   f"Position_DeviceUnit={ch_obj.Position_DeviceUnit}")

        logger.info(f"[Thorlabs.BSM] Подключено устройство: {serial_no}")

    def _ch_obj(self, channel):
        ch_num = channel if isinstance(channel, int) else (channel.value if hasattr(channel, 'value') else int(channel))
        return self._ch[ch_num]

    def set_velocity(self, channel, max_velocity_mm_s=2.0, acceleration_mm_s2=0.5):
        ch_obj = self._ch_obj(channel)
        ch_num = channel if isinstance(channel, int) else (channel.value if hasattr(channel, 'value') else int(channel))
        ch_obj.SetVelocityParams(
            self._System.Decimal(max_velocity_mm_s),
            self._System.Decimal(acceleration_mm_s2)
        )
        time.sleep(0.1)
        vp = ch_obj.GetVelocityParams()
        logger.info(f"[Thorlabs.BSM] Velocity ch={ch_num}: "
                     f"maxVel={vp.MaxVelocity} mm/s, accel={vp.Acceleration} mm/s²")

    def _ch_num(self, channel):
        return channel if isinstance(channel, int) else (channel.value if hasattr(channel, 'value') else int(channel))

    def get_position(self, channel):
        ch_obj = self._ch_obj(channel)
        pos_decimal = ch_obj.Position
        pos_mm = float(str(pos_decimal).replace(',', '.'))
        if pos_mm < 0:
            logger.warning(f"[Thorlabs.BSM] Position ch={self._ch_num(channel)} = {pos_mm} → 0.0")
            return 0.0
        return round(pos_mm, 3)

    def move_relative(self, channel, distance_mkm):
        ch_obj = self._ch_obj(channel)
        ch_num = self._ch_num(channel)
        distance_mm = distance_mkm / 1000.0

        cur_pos = float(str(ch_obj.Position).replace(',', '.'))
        target_pos = cur_pos + distance_mm

        logger.info(f"[Thorlabs.BSM] move_relative ch={ch_num}: "
                     f"{distance_mkm} µm, cur={cur_pos:.4f} mm, target={target_pos:.4f} mm")
        ch_obj.MoveTo(self._System.Decimal(target_pos), self.TIMEOUT * 1000)

        after_pos = float(str(ch_obj.Position).replace(',', '.'))
        actual_delta = after_pos - cur_pos
        logger.info(f"[Thorlabs.BSM] move_relative ch={ch_num} finished: "
                     f"before={cur_pos:.4f}, after={after_pos:.4f}, "
                     f"expected={distance_mm:.4f} mm, actual={actual_delta:.4f} mm")

    def move_home(self, channel):
        ch_obj = self._ch_obj(channel)
        ch_num = self._ch_num(channel)
        logger.info(f"[Thorlabs.BSM] move_home ch={ch_num}")
        try:
            from Thorlabs.MotionControl.GenericMotorCLI.ControlParameters import HomeParameters
            hp = ch_obj.GetHomingParams()
            hp_new = HomeParameters()
            hp_new.Direction = hp.Direction
            hp_new.LimitSwitch = hp.LimitSwitch
            hp_new.Velocity = self._System.Decimal(DEFAULT_HOMING_VELOCITY_MM_S)
            hp_new.OffsetDistance = hp.OffsetDistance
            ch_obj.SetHomingParams(hp_new)
            time.sleep(0.1)
            hp2 = ch_obj.GetHomingParams()
            logger.info(f"[Thorlabs.BSM] ch{ch_num} Homing velocity set: {hp.Velocity} → {hp2.Velocity} mm/s")
        except Exception as e:
            logger.warning(f"[Thorlabs.BSM] ch{ch_num} Could not set homing velocity: {e}")
        ch_obj.Home(self.TIMEOUT * 1000)
        logger.info(f"[Thorlabs.BSM] At home ch={ch_num}")

    def log_channel_status(self, channel, label=""):
        ch_obj = self._ch_obj(channel)
        pos = self.get_position(channel)
        state = ch_obj.State
        enabled = ch_obj.IsEnabled
        logger.info(f"[Thorlabs.BSM] ch={self._ch_num(channel)} [{label}]: "
                     f"pos={pos} mm, state={state}, enabled={enabled}")

    def close(self):
        self.refcount -= 1
        if self.refcount <= 0 and not self._closed:
            self._closed = True
            try:
                for ch_obj in self._ch.values():
                    ch_obj.StopPolling()
                time.sleep(0.3)
                self.device.Disconnect()
                time.sleep(1)
                del self.device
                import gc; gc.collect()
                time.sleep(1)
            except Exception as e:
                logger.warning(f"[Thorlabs.BSM] Ошибка при закрытии: {e}")
            logger.info(f"[Thorlabs.BSM] Closed: {self.serial_no}")


class ThorlabsBSM:
    TOLERANCE = 0.005
    _devices = {}

    def __init__(self, serial_no, channel=1, max_velocity_mm_s=2.0, acceleration_mm_s2=0.5):
        self.channel = channel
        self.is_connected = True

        if serial_no not in self._devices or self._devices[serial_no]._closed:
            self._devices[serial_no] = _BSMConnection(serial_no)
        else:
            self._devices[serial_no].refcount += 1
        self._device = self._devices[serial_no]

        self._device.log_channel_status(self.channel, "init")

        init_pos = self.get_position()
        logger.info(f"[Thorlabs.BSM] Подключено: {serial_no}, channel={channel}, "
                    f"initial_position={init_pos} mm")

    def get_position(self):
        return self._device.get_position(self.channel)

    def move_relative(self, distance_mkm):
        self._device.move_relative(self.channel, distance_mkm)

    def move_home(self):
        self._device.move_home(self.channel)

    def wait_for_stop(self):
        pass

    def close(self):
        if self.is_connected:
            self.is_connected = False
            self._device.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class ThorlabsAxis:
    def __new__(cls, *args, **kwargs):
        return ThorlabsCube(*args, **kwargs)
