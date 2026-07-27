# -*- coding: utf-8 -*-
"""
Thorlabs PM100 series optical power meter driver.

Communicates over USB via PyVISA using SCPI commands.
Supports auto-scanning of connected PM100 devices and
independent power-vs-time recording.

Created on Fri May 28 13:02:47 2021
@author: Ilya
"""
import os
import sys
import csv
import pyvisa as visa
from PyQt5.QtCore import QObject, pyqtSignal
import time
import logging
logger = logging.getLogger(__name__)
from Utils.Loggable import Loggable


def _data_dir():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'data', 'powermeter')


DATA_DIR = _data_dir()


def _get_resource_manager():
    try:
        rm = visa.ResourceManager('@py')
    except Exception:
        rm = visa.ResourceManager()
    return rm


def _check_driver():
    try:
        import libusb_package
        import usb.backend.libusb1
        import usb.core
        backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
        dev = usb.core.find(idVendor=0x1313, idProduct=0x8078, backend=backend)
        return dev is not None
    except Exception:
        return False


DRIVER_MISSING_MSG = (
    "PM100D not found. The Windows USB driver is not installed.\n"
    "Run Hardware/drivers/install_driver.bat as Administrator\n"
    "to install the WinUSB driver (no Thorlabs software needed)."
)


def scan_devices():
    """
    Scan USB for all Thorlabs PM100 series devices.
    Returns list of dicts: [{serial, name, resource}]
    """
    devices = []
    try:
        rm = _get_resource_manager()
        resources = rm.list_resources()
        for res in resources:
            if 'USB' not in res:
                continue
            try:
                h = rm.open_resource(res)
                h.write("*IDN?")
                idn = h.read().strip()
                parts = idn.split(',')
                if len(parts) >= 3 and 'Thorlabs' in idn:
                    name = ' '.join(p.strip() for p in parts[:2])
                    serial = parts[2].strip()
                    devices.append({'serial': serial, 'name': name, 'resource': res})
                    logger.info("Found Thorlabs PM: %s (SN: %s) at %s", name, serial, res)
                h.close()
            except Exception:
                try:
                    h.close()
                except Exception:
                    pass
    except Exception as e:
        logger.warning("Failed to scan for PM100 devices: %s", e)
    return devices


class PowerMeter(QObject, Loggable):
    """
    Thorlabs PM100D optical power meter.

    NOTE: You may need to switch drivers through
    Thorlabs Optical Power Monitor program.

    Uses the PyVISA library to communicate over USB.
    """
    power_received = pyqtSignal(float, float)
    recording_started = pyqtSignal(str)
    recording_stopped = pyqtSignal(str)

    def __init__(self, SerialNumber):
        super().__init__()
        self._serial = SerialNumber
        self._recording = False
        self._record_file = None
        self._record_writer = None
        self._record_start_time = None
        self.device = self._find_device(SerialNumber)

    def _find_device(self, SerialNumber):
        rm = _get_resource_manager()
        resources = rm.list_resources()
        for b in resources:
            if 'USB' not in b:
                continue
            try:
                h = rm.open_resource(b)
                h.write("*IDN?")
                idn = h.read()
                if idn.split(',')[2].strip() == SerialNumber:
                    self.log.info('Connected to powermeter %s', SerialNumber)
                    return h
                h.close()
            except Exception:
                continue
        self.log.info('No powermeter found with serial %s', SerialNumber)
        return None

    def is_connected(self):
        return self.device is not None

    def get_power(self):
        if self.device is None:
            return None
        self.device.write("READ?")
        power = float(self.device.read())
        now = time.time()
        self.power_received.emit(power, now)
        if self._recording and self._record_writer:
            try:
                self._record_writer.writerow([now - self._record_start_time, power])
                self._record_file.flush()
            except Exception as e:
                self.log.error("Recording write error: %s", e)
        return power

    def start_recording(self, filepath=None):
        if self._recording:
            return
        os.makedirs(DATA_DIR, exist_ok=True)
        if filepath is None:
            ts = time.strftime('%Y-%m-%d_%H-%M-%S')
            filepath = os.path.join(DATA_DIR, f'PM100_{self._serial}_{ts}.csv')
        self._record_file = open(filepath, 'w', newline='', encoding='utf-8')
        self._record_writer = csv.writer(self._record_file)
        self._record_writer.writerow(['time_s', 'power_W'])
        self._record_start_time = time.time()
        self._recording = True
        self.log.info("Recording started: %s", filepath)
        self.recording_started.emit(filepath)

    def stop_recording(self):
        if not self._recording:
            return
        self._recording = False
        filepath = self._record_file.name if self._record_file else ''
        try:
            self._record_file.close()
        except Exception:
            pass
        self._record_file = None
        self._record_writer = None
        self._record_start_time = None
        self.log.info("Recording stopped: %s", filepath)
        self.recording_stopped.emit(filepath)

    def close(self):
        self.stop_recording()
        if self.device:
            try:
                self.device.close()
            except Exception:
                pass
            self.device = None

    def __del__(self):
        self.close()


if __name__ == '__main__':
    print("Checking USB driver...")
    if not _check_driver():
        print(DRIVER_MISSING_MSG)
    else:
        print("USB device detected. Scanning VISA...")
    devs = scan_devices()
    print("Found devices:", devs)
    if devs:
        PM = PowerMeter(devs[0]['serial'])
        if PM.is_connected():
            print("Power:", PM.get_power(), "W")
        PM.close()
    else:
        print("No PM100 devices found via VISA.")
