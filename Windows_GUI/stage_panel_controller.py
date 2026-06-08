import logging

logger = logging.getLogger(__name__)

THORLABS = 'THORLABS'


class StageAxisSelector:
    """Single source combo per axis — shows COM ports or Thorlabs serials by type."""

    def __init__(self, name, type_combo, source_combo):
        self.name = name
        self.type_combo = type_combo
        self.source_combo = source_combo
        self._all_ports = []
        self._all_ids = []

        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self._on_type_changed(self.type_combo.currentText())

    def _source_items(self):
        if self.is_thorlabs():
            return ['-'] + self._all_ids
        return ['-'] + self._all_ports

    def _on_type_changed(self, text):
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        for item in self._source_items():
            self.source_combo.addItem(item)
        self.source_combo.setVisible(text != '-')
        self.source_combo.blockSignals(False)

    def _refresh_source(self, taken=None):
        if taken is None:
            taken = set()
        self.source_combo.blockSignals(True)
        current = self.source_combo.currentText()
        self.source_combo.clear()
        for item in self._source_items():
            if item not in taken or item == current:
                self.source_combo.addItem(item)
        idx = self.source_combo.findText(current)
        if idx >= 0:
            self.source_combo.setCurrentIndex(idx)
        else:
            self.source_combo.setCurrentText('-')
        self.source_combo.blockSignals(False)

    def is_disabled(self):
        return self.type_combo.currentText() == '-'

    def is_thorlabs(self):
        return self.type_combo.currentText().upper() == THORLABS

    def get_source(self):
        return self.source_combo.currentText()

    def get_config(self):
        if self.is_disabled():
            return None
        source = self.get_source()
        if source in ('', '-'):
            return None
        cfg = {'type': self.type_combo.currentText()}
        if self.is_thorlabs():
            cfg['serial'] = source
            cfg['thorlabs_type'] = 'KDC'
        else:
            cfg['port'] = source
        return cfg


class StagePanelController:
    """Manages all three axes: pool tracking and mutual exclusion."""

    def __init__(self, ui):
        self.axes = {
            'X': StageAxisSelector('X', ui.comboBox_X, ui.comboBox_SourceX),
            'Y': StageAxisSelector('Y', ui.comboBox_Y, ui.comboBox_SourceY),
            'Z': StageAxisSelector('Z', ui.comboBox_Z, ui.comboBox_SourceZ),
        }
        self._all_ports = []
        self._all_ids = []

        for name, ax in self.axes.items():
            ax.source_combo.currentTextChanged.connect(lambda _, n=name: self._on_source_changed(n))
            ax.type_combo.currentTextChanged.connect(lambda _, n=name: self._on_type_changed(n))

    def _refresh_all(self, changed_axis=None):
        taken_ports = set()
        taken_ids = set()
        for ax_name, ax in self.axes.items():
            if ax_name == changed_axis:
                continue
            if ax.is_disabled():
                continue
            val = ax.get_source()
            if val in ('', '-'):
                continue
            if ax.is_thorlabs():
                taken_ids.add(val)
            else:
                taken_ports.add(val)

        for ax_name, ax in self.axes.items():
            if ax.is_disabled():
                continue
            taken = taken_ids if ax.is_thorlabs() else taken_ports
            ax._refresh_source(taken)

    def _on_source_changed(self, changed_axis):
        self._refresh_all(changed_axis)

    def _on_type_changed(self, changed_axis):
        self._refresh_all(changed_axis)

    def update_ports(self, ports):
        self._all_ports = list(ports)
        for ax in self.axes.values():
            ax._all_ports = list(ports)
            if not ax.is_disabled() and not ax.is_thorlabs():
                ax._on_type_changed(ax.type_combo.currentText())
        self._refresh_all()

    def update_ids(self, ids):
        self._all_ids = list(ids)
        for ax in self.axes.values():
            ax._all_ids = list(ids)
            if ax.is_thorlabs():
                ax._on_type_changed(ax.type_combo.currentText())
        self._refresh_all()

    def get_config(self):
        config = {}
        for name, ax in self.axes.items():
            cfg = ax.get_config()
            if cfg is not None:
                config[name] = cfg
        return config
