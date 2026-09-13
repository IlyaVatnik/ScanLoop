# -*- coding: utf-8 -*-
"""
PairedRecorder: одновременная запись данных осциллографа (scope) и OSA.
Запускается как отдельный QObject в своём потоке через ThreadedMainWindow.add_thread.

Два режима:
  Single  - один кортеж: 1+1 (первый замер scope и OSA)
  Repeat  - непрерывный цикл: кортежи граничат по циклу OSA (старт -> received_spectrum),
            scope-замеры накапливаются в текущий открытый кортеж.

Данные кортежа сохраняются в data/osa_scope/experiment_<дата>/tuple_NNN/:
  scope_k.osc_pkl  / scope_k.csv   - k-ый замер осциллографа
  osa_k.pkl        / osa_k.csv     - спектр OSA
  times.txt                          тайминги

Retry осциллографа: N попыток запроса с паузой, при провале -- ошибка вместо зависания.
Контроль OSA: watchdog QTimer; если спектр не пришёл за osa_timeout - фиксируем потерю.
В Repeat при ошибке одного прибора сохраняется то, что уже получено, и цикл продолжается.
"""
import os
import time
import pickle
import numpy as np
from datetime import datetime

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from Utils.Loggable import Loggable


class _ScopeRetryRunner(Loggable, QObject):
    """Выполняет scope.acquire() в потоке осциллографа с ретраями."""
    finished = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, scope, attempts=3, pause=1.0, timeout=120.0):
        super().__init__()
        self.scope = scope
        self.attempts = attempts
        self.pause = pause
        self.timeout = timeout

    def acquire(self):
        last_err = None
        for attempt in range(1, self.attempts + 1):
            try:
                self.scope.acquire(timeout=self.timeout)
                self.finished.emit()
                return
            except Exception as e:
                last_err = e
                self.log.warning('Scope acquire attempt %d/%d failed: %s',
                                 attempt, self.attempts, e)
                if attempt < self.attempts:
                    time.sleep(self.pause)
        self.failed.emit(str(last_err))


class _TupleRecord(object):
    """Один кортеж записи: папка tuple_NNN, списки scope-замеров и один спектр OSA."""

    def __init__(self, index, experiment_dir):
        self.index = index
        self.folder = os.path.join(experiment_dir, 'tuple_{:03d}'.format(index))
        os.makedirs(self.folder, exist_ok=True)
        self.scope_records = list()
        self.osa_record = None
        self.opened_at = time.time()
        self._times_path = os.path.join(self.folder, 'times.txt')
        with open(self._times_path, 'a', encoding='utf-8') as f:
            f.write('tuple #{:d} opened at {:.6f}\n'.format(index, self.opened_at))

    def add_scope(self, X, Y, channels, timestamp):
        record = dict(X=X, Y=Y, channels=list(channels),
                      timestamp=timestamp, t=timestamp - self.opened_at)
        self.scope_records.append(record)
        with open(self._times_path, 'a', encoding='utf-8') as f:
            f.write('  scope #{:d} at {:.6f} (t={:.6f}s), channels={}\n'.format(
                len(self.scope_records), timestamp, record['t'], list(channels)))

    def add_osa(self, wavelengths, spectra, channels, timestamp):
        self.osa_record = dict(wavelengths=wavelengths, spectra=spectra,
                               channels=list(channels),
                               timestamp=timestamp, t=timestamp - self.opened_at)
        with open(self._times_path, 'a', encoding='utf-8') as f:
            f.write('  osa #{:d} at {:.6f} (t={:.6f}s)\n'.format(
                len(self.osa_record), timestamp, self.osa_record['t']))

    def close(self):
        """Сохраняет всё на диск. Пишет osa_1.* и scope_k.* (pickle + CSV)."""
        for k, rec in enumerate(self.scope_records, start=1):
            prefix = os.path.join(self.folder, 'scope_{:d}'.format(k))
            with open(prefix + '.osc_pkl', 'wb') as f:
                pickle.dump(rec, f)
            self._write_scope_csv(prefix + '.csv', rec)
        if self.osa_record is not None:
            prefix = os.path.join(self.folder, 'osa_1')
            with open(prefix + '.pkl', 'wb') as f:
                pickle.dump(self.osa_record, f)
            self._write_osa_csv(prefix + '.csv', self.osa_record)
        with open(self._times_path, 'a', encoding='utf-8') as f:
            f.write('tuple #{:d} closed at {:.6f}\n'.format(self.index, time.time()))

    @staticmethod
    def _write_scope_csv(path, rec):
        Y = list(rec['Y'])
        if not Y:
            return
        n = min([len(rec['X'])] + [len(y) for y in Y])
        if n == 0:
            return
        header = ['X'] + ['CH{}'.format(c) for c in rec['channels']]
        matrix = np.column_stack([rec['X'][:n]] + [y[:n] for y in Y])
        np.savetxt(path, matrix, delimiter=',', header=','.join(header),
                   comments='', encoding='utf-8')

    @staticmethod
    def _write_osa_csv(path, rec):
        wavelengths = np.asarray(rec['wavelengths']).ravel()
        spectra = rec['spectra']
        if len(wavelengths) == 0 or len(spectra) == 0:
            return
        y = np.asarray(spectra[0]).ravel()
        n = min(len(wavelengths), len(y))
        if n == 0:
            return
        np.savetxt(path, np.column_stack([wavelengths[:n], y[:n]]),
                   delimiter=',', header='wavelength,spectrum', comments='',
                   encoding='utf-8')


class PairedRecorder(Loggable, QObject):
    """Запись парных измерений OSA + осциллограф."""

    S_print = pyqtSignal(str)
    S_print_error = pyqtSignal(str)
    S_finished = pyqtSignal()
    S_running = pyqtSignal(bool)
    S_status = pyqtSignal(str)
    S_start_osa = pyqtSignal()
    S_start_scope = pyqtSignal()

    def __init__(self, root=None, retry_attempts=3, retry_pause=1.0,
                 scope_timeout=120.0, osa_timeout=600.0):
        super().__init__()
        self.root = root or os.path.join(os.getcwd(), 'data', 'osa_scope')
        self.scope = None
        self.osa = None
        self.retry_attempts = retry_attempts
        self.retry_pause = retry_pause
        self.scope_timeout = scope_timeout
        self.osa_timeout = osa_timeout

        self.is_running = False
        self.repeat = False
        self.current_tuple = None
        self.pending_scope = None
        self.cycle_count = 0
        self.experiment_dir = None
        self._scope_runner = None

        self._osa_watchdog = QTimer(self)
        self._osa_watchdog.setSingleShot(True)
        self._osa_watchdog.timeout.connect(self._on_osa_timeout)

    def set_devices(self, scope, osa):
        """Подключается к приборам. Вызывается из MainWindow после connect_scope/connect_OSA."""
        if scope is not None and scope is not self.scope:
            if self.scope is not None:
                self._disconnect_device(self.scope.received_data, self.on_scope_data)
            self.scope = scope
            self.scope.received_data.connect(self.on_scope_data)
        if osa is not None and osa is not self.osa:
            if self.osa is not None:
                self._disconnect_device(self.osa.received_spectrum, self.on_osa_data)
            self.osa = osa
            self.osa.received_spectrum.connect(self.on_osa_data)
        self._setup_scope_runner()

    @staticmethod
    def _disconnect_device(signal, slot):
        try:
            signal.disconnect(slot)
        except TypeError:
            pass

    def devices_ready(self):
        return self.scope is not None and self.osa is not None

    def _setup_scope_runner(self):
        if self.scope is None or self._scope_runner is not None:
            return
        runner = _ScopeRetryRunner(self.scope, attempts=self.retry_attempts,
                                   pause=self.retry_pause, timeout=self.scope_timeout)
        runner.moveToThread(self.scope.thread())
        runner.finished.connect(self.on_scope_acquired)
        runner.failed.connect(self.on_scope_acquire_failed)
        self.S_start_scope.connect(runner.acquire)
        self._scope_runner = runner

    def _start_experiment(self):
        name = datetime.now().strftime('experiment_%Y-%m-%d_%H-%M-%S')
        self.experiment_dir = os.path.join(self.root, name)
        os.makedirs(self.experiment_dir, exist_ok=True)
        self.S_print.emit('Paired record started: {}'.format(self.experiment_dir))

    def _open_tuple(self):
        self.cycle_count += 1
        self.current_tuple = _TupleRecord(self.cycle_count, self.experiment_dir)
        if self.pending_scope is not None:
            self.current_tuple.add_scope(*self.pending_scope)
            self.pending_scope = None
        self.S_status.emit('Recording tuple #{:d}'.format(self.cycle_count))
        self.log.info('Opened tuple #%d', self.cycle_count)

    def _close_tuple(self):
        if self.current_tuple is None:
            return
        self.current_tuple.close()
        folder = self.current_tuple.folder
        idx = self.current_tuple.index
        self.current_tuple = None
        self.S_print.emit('Tuple #{:d} saved: {}'.format(idx, folder))
        self.log.info('Closed tuple #%d', idx)

    def _finish(self):
        self.is_running = False
        self.repeat = False
        self.current_tuple = None
        self._osa_watchdog.stop()
        self.S_status.emit('Idle')
        self.S_finished.emit()
        self.S_running.emit(False)

    def start_single(self):
        if not self.devices_ready():
            self.S_print_error.emit('Paired record: both OSA and scope must be connected')
            return
        if self.is_running:
            self.S_print_error.emit('Paired record is already running')
            return
        self.is_running = True
        self.repeat = False
        self.cycle_count = 0
        self.pending_scope = None
        self._start_experiment()
        self._open_tuple()
        self.S_print.emit('Single paired measurement: 1 scope + 1 OSA')
        self.S_running.emit(True)
        self._start_cycles()

    def start_repeat(self):
        if not self.devices_ready():
            self.S_print_error.emit('Paired record: both OSA and scope must be connected')
            return
        if self.is_running:
            self.S_print_error.emit('Paired record is already running')
            return
        self.is_running = True
        self.repeat = True
        self.cycle_count = 0
        self.pending_scope = None
        self._start_experiment()
        self._open_tuple()
        self.S_print.emit('Repeat paired measurement started')
        self.S_running.emit(True)
        self._start_cycles()

    def _start_cycles(self):
        self._osa_watchdog.start(int(self.osa_timeout * 1000))
        self.S_start_osa.emit()
        self.S_start_scope.emit()

    def stop(self):
        if not self.is_running:
            return
        self.S_print.emit('Paired record stopped by user')
        self._close_tuple()
        self._finish()

    def on_scope_acquired(self):
        pass

    def on_scope_acquire_failed(self, error):
        if not self.is_running:
            return
        self.log.error('Scope acquisition failed after %d attempts: %s',
                       self.retry_attempts, error)
        self.S_print_error.emit('Scope: signal lost ({}). {}'.format(
            error, 'Tuple saved, repeat continues' if self.repeat else 'Record stopped'))
        self._handle_loss()

    def _handle_loss(self):
        if self.current_tuple is not None:
            self._close_tuple()
        if self.repeat:
            self._open_tuple()
            self._osa_watchdog.start(int(self.osa_timeout * 1000))
            self.S_start_osa.emit()
        else:
            self._finish()

    def on_scope_data(self, X, Y, channels):
        if not self.is_running:
            return
        ts = time.time()
        if self.current_tuple is not None:
            self.current_tuple.add_scope(X, Y, channels, ts)
            if self.repeat:
                self.S_start_scope.emit()
            else:
                self._maybe_finish_single()
        else:
            self.pending_scope = (X, Y, channels, ts)
            self._maybe_finish_single()

    def on_osa_data(self, wavelengths, spectra, channels):
        if not self.is_running:
            return
        self._osa_watchdog.stop()
        ts = time.time()
        if self.current_tuple is not None:
            self.current_tuple.add_osa(wavelengths, spectra, channels, ts)
        if self.repeat:
            self._close_tuple()
            self._open_tuple()
            self._osa_watchdog.start(int(self.osa_timeout * 1000))
            self.S_start_osa.emit()
        else:
            self._maybe_finish_single()

    def _maybe_finish_single(self):
        """Single заканчивается только когда получены и OSA-спектр, и scope-замер."""
        if not self.is_running or self.repeat:
            return
        t = self.current_tuple
        if t is not None and t.osa_record is not None and t.scope_records:
            self._close_tuple()
            self.S_print.emit('Single paired measurement finished')
            self._finish()

    def _on_osa_timeout(self):
        if not self.is_running:
            return
        self.log.error('OSA spectrum not received within %.1f s', self.osa_timeout)
        self.S_print_error.emit('OSA: no spectrum within {:.1f} s. {}'.format(
            self.osa_timeout, 'Tuple saved, repeat continues' if self.repeat else 'Record stopped'))
        self._handle_loss()
