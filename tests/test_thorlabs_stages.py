from ctypes import c_int, c_short
from unittest.mock import MagicMock
import pytest

from tests.conftest import get_bsm_mock, get_kdc_mock


def _v(obj):
    return obj.value if hasattr(obj, 'value') else obj


# ──────────────────────────────────────────────
# 1. scan — фильтрация каналов
# ──────────────────────────────────────────────
class TestScan:
    def test_scan_filters_invalid_channels(self):
        from Hardware.Stages.Thorlabs.thorlabs_stages import get_thorlabs_serials
        bsm = get_bsm_mock()
        bsm.SBC_IsChannelValid.side_effect = lambda ser, ch: _v(ch) <= 2
        bsm.SBC_GetNumChannels.return_value = c_short(3)
        bsm.SBC_Open.return_value = 0

        devices = get_thorlabs_serials()
        bsm_devices = [d for d in devices if d["type"] == "BSM"]
        assert len(bsm_devices) == 1

        channels = bsm_devices[0].get("channels", [])
        assert channels == [1, 2]
        assert 3 not in channels

    def test_scan_all_channels_valid(self):
        from Hardware.Stages.Thorlabs.thorlabs_stages import get_thorlabs_serials
        bsm = get_bsm_mock()
        bsm.SBC_IsChannelValid.side_effect = lambda ser, ch: True
        bsm.SBC_GetNumChannels.return_value = c_short(3)
        bsm.SBC_Open.return_value = 0

        devices = get_thorlabs_serials()
        bsm_devs = [d for d in devices if d["type"] == "BSM"]
        assert bsm_devs[0]["channels"] == [1, 2, 3]

    def test_scan_channels_one_based(self):
        from Hardware.Stages.Thorlabs.thorlabs_stages import get_thorlabs_serials
        bsm = get_bsm_mock()
        bsm.SBC_IsChannelValid.side_effect = lambda ser, ch: True
        bsm.SBC_GetNumChannels.return_value = c_short(2)
        bsm.SBC_Open.return_value = 0

        devices = get_thorlabs_serials()
        bsm_devs = [d for d in devices if d["type"] == "BSM"]
        assert bsm_devs[0]["channels"] == [1, 2]
        assert 0 not in bsm_devs[0]["channels"]


# ──────────────────────────────────────────────
# 2. init — последовательность и ошибки
# ──────────────────────────────────────────────
class TestInitSequence:
    def test_load_settings_and_enable_channel_called(self):
        """SBC_LoadSettings и SBC_EnableChannel вызываются при init"""
        bsm = get_bsm_mock()
        bsm.reset_mock()

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=1)
        assert stage.is_connected

        assert bsm.SBC_LoadSettings.call_count >= 1
        assert bsm.SBC_EnableChannel.call_count >= 1
        stage.close()

    def test_init_success(self):
        bsm = get_bsm_mock()
        bsm.reset_mock()

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=1)
        assert stage.is_connected
        assert _v(stage.channel) == 1
        stage.close()

    def test_default_channel_is_one(self):
        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        assert ThorlabsBSM.__init__.__defaults__[0] == 1

    def test_polling_called_in_init(self):
        """SBC_StartPolling вызывается в ThorlabsBSM.__init__"""
        bsm = get_bsm_mock()
        bsm.reset_mock()

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=1)
        assert bsm.SBC_StartPolling.call_count >= 1
        stage.close()

    def test_request_position_in_init(self):
        """SBC_RequestPosition вызывается перед SBC_GetPosition в __init__"""
        bsm = get_bsm_mock()
        bsm.reset_mock()

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=1)
        assert bsm.SBC_RequestPosition.call_count >= 1
        stage.close()


# ──────────────────────────────────────────────
# 3. velocity — параметры
# ──────────────────────────────────────────────
class TestVelocity:
    def test_set_velocity_arg_order(self):
        """SBC_SetVelParams вызывается с (maxVel, accel), а не (accel, maxVel)"""
        bsm = get_bsm_mock()
        bsm.reset_mock()

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=1)
        stage.close()

        set_call = bsm.SBC_SetVelParams.call_args
        assert set_call is not None
        assert len(set_call[0]) == 4
        args = set_call[0]
        # args: (serial, channel, maxVel, accel)
        assert _v(args[2]) == 1000   # maxVel: 2.0 mm/s / 0.002 = 1000
        assert _v(args[3]) == 250    # accel:  0.5 mm/s² / 0.002 = 250

    def test_custom_velocity_params(self):
        """Кастомные velocity/accel пробрасываются в SBC_SetVelParams"""
        bsm = get_bsm_mock()
        bsm.reset_mock()

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=1,
                            max_velocity_mm_s=5.0, acceleration_mm_s2=1.0)
        stage.close()

        set_call = bsm.SBC_SetVelParams.call_args
        args = set_call[0]
        assert _v(args[2]) == 2500   # 5.0 / 0.002
        assert _v(args[3]) == 500    # 1.0 / 0.002

    def test_diagnostic_get_vel_params_called(self):
        """SBC_GetVelParams вызывается ДО и ПОСЛЕ установки скорости"""
        bsm = get_bsm_mock()
        bsm.reset_mock()

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=1)
        stage.close()

        # SBC_GetVelParams вызывается минимум 2 раза (до и после set)
        assert bsm.SBC_GetVelParams.call_count >= 2

    def test_default_velocity_values(self):
        """Дефолтные значения: maxVel=2.0 мм/с, accel=0.5 мм/с²"""
        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        defaults = ThorlabsBSM.__init__.__defaults__
        # (channel=1, max_velocity_mm_s=2.0, acceleration_mm_s2=0.5)
        assert defaults[0] == 1      # channel
        assert defaults[1] == 2.0    # max_velocity_mm_s
        assert defaults[2] == 0.5    # acceleration_mm_s2


# ──────────────────────────────────────────────
# 4. move_relative — poll loop
# ──────────────────────────────────────────────
class TestMoveRelative:
    def _make_stage(self, channel=2):
        bsm = get_bsm_mock()
        bsm.SBC_GetPosition.return_value = c_int(100)
        bsm.SBC_Open.return_value = 0

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()
        return ThorlabsBSM("70864299", channel=channel)

    def test_completes_on_stable_position(self):
        bsm = get_bsm_mock()
        bsm.SBC_Open.return_value = 0

        values = [100, 100, 100]
        def pos_side(*a):
            return c_int(values.pop(0)) if values else c_int(100)
        bsm.SBC_GetPosition = MagicMock(side_effect=pos_side)

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=2)
        stage.move_relative(40)
        stage.close()

    def test_raises_timeout_on_no_stabilization(self):
        bsm = get_bsm_mock()
        bsm.SBC_Open.return_value = 0

        vals = list(range(500, 0, -1))
        def pos_side(*a):
            return c_int(vals.pop(0)) if vals else c_int(0)
        bsm.SBC_GetPosition = MagicMock(side_effect=pos_side)

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        from Hardware.Stages.Thorlabs.thorlabs_stages import _BSMConnection
        _BSMConnection.TIMEOUT = 0.5

        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=2)
        with pytest.raises(TimeoutError, match="move_relative timeout"):
            stage.move_relative(40)
        stage.close()

    def test_timeout_when_position_never_stabilizes(self):
        bsm = get_bsm_mock()
        bsm.SBC_Open.return_value = 0

        counter = [0]
        def pos_side(*a):
            counter[0] += 1
            return c_int(counter[0])
        bsm.SBC_GetPosition = MagicMock(side_effect=pos_side)

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        from Hardware.Stages.Thorlabs.thorlabs_stages import _BSMConnection
        _BSMConnection.TIMEOUT = 0.5

        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=2)
        with pytest.raises(TimeoutError, match="move_relative timeout"):
            stage.move_relative(40)
        stage.close()

    def test_move_relative_sends_correct_steps(self):
        from Hardware.Stages.Thorlabs.thorlabs_stages import _BSMConnection
        saved_timeout = _BSMConnection.TIMEOUT
        _BSMConnection.TIMEOUT = 30

        bsm = get_bsm_mock()
        bsm.SBC_Open.return_value = 0

        bsm.SBC_GetPosition = MagicMock(return_value=c_int(100))

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=2)
        stage.move_relative(-40)
        stage.close()
        _BSMConnection.TIMEOUT = saved_timeout

        set_dist_calls = [
            c for c in bsm.method_calls
            if c[0] == "SBC_SetMoveRelativeDistance"
        ]
        assert len(set_dist_calls) >= 1
        args = set_dist_calls[-1].args
        steps_arg = args[-1]
        assert _v(steps_arg) == -20


# ──────────────────────────────────────────────
# 5. channel init — unknown position handling
# ──────────────────────────────────────────────
class TestChannelInit:
    def test_unknown_sets_counter_when_can_move_without_homing(self):
        bsm = get_bsm_mock()
        bsm.SBC_Open.return_value = 0
        bsm.SBC_GetPosition.return_value = c_int(-1)
        bsm.SBC_CanMoveWithoutHomingFirst.return_value = True
        bsm.SBC_CanHome.return_value = True

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=2)
        stage.close()

        assert bsm.SBC_CanMoveWithoutHomingFirst.called
        assert bsm.SBC_SetPositionCounter.called
        assert bsm.SBC_Home.call_count == 0

    def test_unknown_homes_when_cannot_move_without_homing(self):
        bsm = get_bsm_mock()
        bsm.reset_mock()
        bsm.SBC_Open.return_value = 0
        bsm.SBC_GetPosition.return_value = c_int(-1)
        bsm.SBC_CanMoveWithoutHomingFirst.return_value = False
        bsm.SBC_CanHome.return_value = True

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=2)
        stage.close()

        assert bsm.SBC_CanMoveWithoutHomingFirst.called
        assert bsm.SBC_CanHome.called
        assert bsm.SBC_Home.called
        assert bsm.SBC_SetPositionCounter.call_count == 0

    def test_unknown_raises_when_neither_option(self):
        bsm = get_bsm_mock()
        bsm.SBC_Open.return_value = 0
        bsm.SBC_GetPosition.return_value = c_int(-1)
        bsm.SBC_CanMoveWithoutHomingFirst.return_value = False
        bsm.SBC_CanHome.return_value = False

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        with pytest.raises(RuntimeError, match="uninitialized"):
            ThorlabsBSM("70864299", channel=2)

    def test_known_position_skips_init_checks(self):
        bsm = get_bsm_mock()
        bsm.reset_mock()
        bsm.SBC_Open.return_value = 0
        bsm.SBC_GetPosition.return_value = c_int(60)

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=1)
        stage.close()

        assert bsm.SBC_CanMoveWithoutHomingFirst.call_count == 0
        assert bsm.SBC_SetPositionCounter.call_count == 0
        assert bsm.SBC_Home.call_count == 0

    def test_homing_velocity_set_before_home(self):
        """SetHomingVelocity вызывается перед Home при неизвестной позиции"""
        bsm = get_bsm_mock()
        bsm.reset_mock()
        bsm.SBC_Open.return_value = 0
        bsm.SBC_GetPosition.return_value = c_int(-1)
        bsm.SBC_CanMoveWithoutHomingFirst.return_value = False
        bsm.SBC_CanHome.return_value = True

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM
        ThorlabsBSM._devices.clear()

        stage = ThorlabsBSM("70864299", channel=2)
        stage.close()

        assert bsm.SBC_SetHomingVelocity.call_count >= 1
        assert bsm.SBC_Home.called


# ──────────────────────────────────────────────
# 6. KDC — базовые проверки
# ──────────────────────────────────────────────
class TestKDC:
    def test_init_success(self):
        kdc = get_kdc_mock()
        kdc.CC_Open.return_value = 0

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsCube
        stage = ThorlabsCube("70864299")
        assert stage.is_connected
        stage.close()

    def test_init_fail_raises(self):
        kdc = get_kdc_mock()
        kdc.CC_Open.return_value = 1

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsCube
        with pytest.raises(RuntimeError, match="Не удалось подключиться"):
            ThorlabsCube("70864299")

    def test_move_relative(self):
        kdc = get_kdc_mock()
        kdc.CC_Open.return_value = 0

        from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsCube
        stage = ThorlabsCube("70864299")
        stage.move_relative(100)
        stage.close()
