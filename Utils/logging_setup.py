# -*- coding: utf-8 -*-
"""
Centralized logging setup.
Creates Logs/<run_timestamp>/ with rotated log files,
installs global exception hooks, and captures Qt diagnostics.
"""

import logging
from logging.handlers import RotatingFileHandler
import sys
import os
from datetime import datetime

logging.raiseExceptions = False


def setup_logging(logs_root_dir="Logs", max_bytes=50*1024*1024, backup_count=10):
    run_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = os.path.join(os.getcwd(), logs_root_dir, run_stamp)
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"scanloop_{run_stamp}.log")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(name)s(%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if not getattr(sys, "frozen", False):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logging.info("=== Application Started ===")
    logging.info("Python: %s", sys.version.replace("\n", " "))
    logging.info("Platform: %s", sys.platform)
    logging.info("Executable: %s", sys.executable)
    logging.info("Log directory: %s", log_dir)
    _log_package_versions()

    return logger, log_dir


def _log_package_versions():
    packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("matplotlib", "matplotlib"),
        ("PyQt5", "PyQt5"),
        ("pyvisa", "pyvisa"),
        ("pyserial", "serial"),
    ]
    for name, import_name in packages:
        try:
            mod = __import__(import_name)
            ver = getattr(mod, "__version__", None)
            if ver is None:
                ver = "unknown"
            logging.info("%s: %s", name, ver)
        except ImportError:
            logging.warning("%s: NOT INSTALLED", name)


def install_exception_hooks():
    def exception_hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, (SystemExit, KeyboardInterrupt)):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logging.critical(
            "UNHANDLED EXCEPTION",
            exc_info=(exc_type, exc_value, exc_tb)
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = exception_hook

    if hasattr(sys, "unraisablehook"):
        original_unraisablehook = sys.unraisablehook

        def unraisable_hook(unraisable):
            logging.critical(
                "UNRAISABLE: %s", str(unraisable.exc_value)
            )
            original_unraisablehook(unraisable)

        sys.unraisablehook = unraisable_hook


def install_qt_message_handler():
    try:
        from PyQt5.QtCore import qInstallMessageHandler, QtMsgType
        import os as _os

        IS_DEV_MODE = _os.environ.get("SCANLOOP_DEV", "").lower() in ("1", "true", "yes")

        def handler(mode, context, message):
            if mode == QtMsgType.QtDebugMsg and not IS_DEV_MODE:
                return
            level_map = {
                QtMsgType.QtDebugMsg: logging.DEBUG,
                QtMsgType.QtInfoMsg: logging.INFO,
                QtMsgType.QtWarningMsg: logging.WARNING,
                QtMsgType.QtCriticalMsg: logging.ERROR,
                QtMsgType.QtFatalMsg: logging.CRITICAL,
            }
            logging.log(
                level_map.get(mode, logging.INFO),
                "[Qt] (file=%s, line=%d): %s",
                context.file(), context.line(), message
            )

        qInstallMessageHandler(handler)
    except Exception:
        logging.warning("Failed to install Qt message handler", exc_info=True)


class SafeQApplication:
    def __new__(cls, *args, **kwargs):
        from PyQt5 import QtWidgets as _QtW

        class _SafeQApp(_QtW.QApplication):
            def __init__(self, *a, **kw):
                super().__init__(*a, **kw)
                self._last_error_time = 0.0
                self._error_count = 0
                self._error_suppressed = 0

            def notify(self, receiver, event):
                try:
                    return super().notify(receiver, event)
                except (SystemExit, KeyboardInterrupt):
                    raise
                except Exception:
                    import time as _time
                    now = _time.time()
                    if now - self._last_error_time > 1.0:
                        if self._error_suppressed:
                            try:
                                logging.critical(
                                    "Suppressed %d notify errors in the last second",
                                    self._error_suppressed
                                )
                            except Exception:
                                pass
                        self._error_count = 0
                        self._error_suppressed = 0
                        self._last_error_time = now

                    self._error_count += 1

                    if self._error_count <= 5:
                        try:
                            r = repr(receiver) if receiver is not None else "None"
                        except RuntimeError:
                            r = "<deleted C++ object>"
                        try:
                            e = event.type() if event is not None else "None"
                        except RuntimeError:
                            e = "<deleted C++ object>"
                        logging.critical(
                            "Unhandled exception in notify(receiver=%s, event=%s)",
                            r, e, exc_info=True
                        )
                    else:
                        self._error_suppressed += 1

                    return False

        return _SafeQApp(*args, **kwargs)
