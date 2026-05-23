# -*- coding: utf-8 -*-
import logging


class Loggable:
    @property
    def log(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(f"ScanLoop.{self.__class__.__name__}")
        return self._logger
    
    def set_log_level(self, level):
        self.log.setLevel(level)
