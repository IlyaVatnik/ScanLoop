# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 16:37:13 2026

@author: Александр
"""
# Hardware/Stages/stages_manager.py
__date__ = '2026.05.11'
__version__ = '2.5.0'

import logging
import traceback
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)

try:
    from Hardware.Stages.Standa.standa_stages import StandaAxis
except ImportError as e:
    logger.warning(f"Не удалось загрузить модуль Standa: {e}")
    StandaAxis = None

try:
    from Hardware.Stages.LBTEK.lbtek_stages import LBTEKAxis
except ImportError as e:
    logger.warning(f"Не удалось загрузить модуль LBTEK: {e}")
    LBTEKAxis = None

try:
    from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsCube, ThorlabsBSM
except (ImportError, FileNotFoundError) as e:
    logger.warning(f"Не удалось загрузить модуль Thorlabs: {e}")
    ThorlabsCube = ThorlabsBSM = None


class Stages(QObject):
    connected = pyqtSignal()
    stopped = pyqtSignal()
    S_print_error = pyqtSignal(str)

    def __init__(self, config=None):
        super().__init__()
        self.axes = {'X': None, 'Y': None, 'Z': None}
        self.abs_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.relative_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self.zero_position = {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self._is_moving = False

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(300)
        self._poll_timer.timeout.connect(self._on_poll_timer)

        if config:
            self.setup_stages(config)

    def _on_poll_timer(self):
        """Опрос реального положения столиков при простое (для отслеживания ручного вращения крутилок)"""
        if self._is_moving:
            return
        changed = False
        for key, axis_obj in self.axes.items():
            if axis_obj is not None:
                try:
                    pos = round(axis_obj.get_position(), 2)
                    if abs(self.abs_position[key] - pos) >= 0.01:
                        self.abs_position[key] = pos
                        changed = True
                except Exception:
                    pass
        if changed:
            self.update_relative_positions()
            self.stopped.emit()

    def setup_stages(self, config):
        driver_map = {
            'STANDA': StandaAxis,
            'LBTEK': LBTEKAxis,
        }

        for axis_key, params in config.items():
            if params is None:
                continue
            try:
                stage_type = params['type'].upper()
                serial = params.get('serial', params.get('port', ''))

                if stage_type == 'THORLABS':
                    raw = serial
                    if not raw:
                        continue
                    if 'B' in raw and raw[0].isdigit():
                        channel = int(raw[0])
                        serial = raw[2:]
                        vel = params.get('velocity', 2.0)
                        acc = params.get('acceleration', 0.5)
                        if ThorlabsBSM:
                            self.axes[axis_key] = ThorlabsBSM(serial, channel, vel, acc)
                        else:
                            continue
                    elif raw.startswith('B'):
                        serial = raw[1:]
                        vel = params.get('velocity', 2.0)
                        acc = params.get('acceleration', 0.5)
                        if ThorlabsBSM:
                            self.axes[axis_key] = ThorlabsBSM(serial, 0, vel, acc)
                        else:
                            continue
                    elif raw.startswith('K'):
                        serial = raw[1:]
                        if ThorlabsCube:
                            self.axes[axis_key] = ThorlabsCube(serial)
                        else:
                            continue
                    else:
                        if ThorlabsCube:
                            self.axes[axis_key] = ThorlabsCube(raw)
                        else:
                            continue
                else:
                    driver_class = driver_map.get(stage_type)
                    if driver_class is None:
                        self.S_print_error.emit(f"Неизвестный тип подвижки: {stage_type}")
                        continue
                    port = params.get('port', '')
                    self.axes[axis_key] = driver_class(port)

                logger.info(f"Ось {axis_key} ({stage_type} на {serial}) успешно инициализирована.")

            except Exception as e:
                logger.error(f"Ошибка инициализации оси {axis_key}:\n{traceback.format_exc()}")
                self.S_print_error.emit(f"Ошибка инициализации оси {axis_key}: {e}")

        self.update_all_absolute_positions()

        if any(ax is not None for ax in self.axes.values()):
            self._poll_timer.start()
            self.connected.emit()

    def shiftOnArbitrary(self, key: str, distance: float):
        logger.info(f"[Stages.shiftOnArbitrary] key={key}, distance={distance}")
        axis_obj = self.axes.get(key)

        if axis_obj is None:
            self.S_print_error.emit(f"Ось {key} не подключена.")
            return

        self._is_moving = True
        try:
            axis_obj.move_relative(round(distance, 2))
            if hasattr(axis_obj, 'wait_for_stop'):
                axis_obj.wait_for_stop()
            logger.info(f"[Stages.shiftOnArbitrary] move_relative завершён")
            self.abs_position[key] = round(axis_obj.get_position(), 2)
            self.update_relative_positions()
            self.stopped.emit()
            logger.info(f"[Stages.shiftOnArbitrary] stopped.emit() отправлен, pos={self.abs_position[key]}")

        except Exception as e:
            logger.error(f"[Stages.shiftOnArbitrary] ИСКЛЮЧЕНИЕ:\n{traceback.format_exc()}")
            self.S_print_error.emit(f"Ошибка при движении оси {key}: {e}")
        finally:
            self._is_moving = False

    def move_home(self, key: str):
        axis_obj = self.axes.get(key)
        if axis_obj is None:
            return
        self._is_moving = True
        try:
            axis_obj.move_home()
            if hasattr(axis_obj, 'wait_for_stop'):
                axis_obj.wait_for_stop()
            self.update_all_absolute_positions()
            self.stopped.emit()
        except Exception as e:
            logger.error(f"[Stages.move_home] ИСКЛЮЧЕНИЕ:\n{traceback.format_exc()}")
            self.S_print_error.emit(f"Ошибка move_home оси {key}: {e}")
        finally:
            self._is_moving = False

    def set_zero_positions(self, zeros_list):
        self.zero_position['X'] = round(float(zeros_list[0]), 2)
        self.zero_position['Y'] = round(float(zeros_list[1]), 2)
        self.zero_position['Z'] = round(float(zeros_list[2]), 2)
        self.update_relative_positions()

    def update_relative_positions(self):
        for key in ['X', 'Y', 'Z']:
            self.relative_position[key] = round(self.abs_position[key] - self.zero_position[key], 2)

    def update_all_absolute_positions(self):
        for key, axis_obj in self.axes.items():
            if axis_obj is not None:
                try:
                    pos = round(axis_obj.get_position(), 2)
                    self.abs_position[key] = pos
                    logger.debug(f"[Stages] update_position axis={key}: {pos} um")
                except Exception as e:
                    logger.error(f"Не удалось прочитать позицию оси {key}: {traceback.format_exc()}")
                    self.abs_position[key] = 0.0
        self.update_relative_positions()
        logger.debug(f"[Stages] abs_positions: {self.abs_position}")

    def close_all(self):
        try:
            if hasattr(self, '_poll_timer') and self._poll_timer is not None:
                self._poll_timer.stop()
        except (RuntimeError, TypeError):
            pass
        for key, axis_obj in self.axes.items():
            if axis_obj is not None:
                try:
                    axis_obj.close()
                except Exception as e:
                    logger.error(f"Ошибка закрытия оси {key}: {e}")

    def __del__(self):
        try:
            self.close_all()
        except Exception:
            pass