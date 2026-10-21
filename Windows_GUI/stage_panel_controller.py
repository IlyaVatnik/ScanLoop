import logging

logger = logging.getLogger(__name__)

THORLABS = 'THORLABS'


class StageAxisSelector:
    """Single source combo per axis — shows COM ports or Thorlabs serials by type,
    and exposes acceleration and max velocity for Thorlabs Cube stages."""

    def __init__(self, name, type_combo, source_combo, accel_widgets=None, vel_widgets=None):
        self.name = name
        self.type_combo = type_combo
        self.source_combo = source_combo
        self.accel_widgets = accel_widgets or ()
        self.vel_widgets = vel_widgets or ()
        self._all_ports = []
        self._all_ids = []

        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.source_combo.currentTextChanged.connect(self._on_source_changed)
        self._on_type_changed(self.type_combo.currentText())
        self._update_speed_visibility()

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
        self._update_speed_visibility()

    def _on_source_changed(self, text):
        self._update_speed_visibility()

    def _update_speed_visibility(self):
        is_cube = self.is_thorlabs_cube()
        for w in self.accel_widgets:
            w.setVisible(is_cube)
        for w in self.vel_widgets:
            w.setVisible(is_cube)

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
        self._update_speed_visibility()

    def is_disabled(self):
        return self.type_combo.currentText() == '-'

    def is_thorlabs(self):
        return self.type_combo.currentText().upper() == THORLABS

    def is_thorlabs_cube(self):
        return self.is_thorlabs() and self.get_source().startswith('K')

    def get_source(self):
        return self.source_combo.currentText()

    def get_velocity(self) -> float:
        if self.vel_widgets and len(self.vel_widgets) >= 2:
            try:
                return float(str(self.vel_widgets[1].text()).replace(',', '.'))
            except Exception:
                return 2.0
        return 2.0

    def get_acceleration(self) -> float:
        if self.accel_widgets and len(self.accel_widgets) >= 2:
            try:
                return float(str(self.accel_widgets[1].text()).replace(',', '.'))
            except Exception:
                return 1.5
        return 1.5

    def get_config(self):
        if self.is_disabled():
            return None
        source = self.get_source()
        if source in ('', '-'):
            return None
        cfg = {'type': self.type_combo.currentText()}
        if self.is_thorlabs():
            cfg['serial'] = source
            if self.is_thorlabs_cube():
                cfg['velocity'] = self.get_velocity()
                cfg['acceleration'] = self.get_acceleration()
        else:
            cfg['port'] = source
        return cfg


class StagePanelController:
    """Manages all three axes: pool tracking, mutual exclusion, and velocity/accel parameters."""

    def __init__(self, ui):
        self.ui = ui
        self.axes = {
            'X': StageAxisSelector(
                'X', ui.comboBox_X, ui.comboBox_SourceX,
                accel_widgets=(getattr(ui, 'label_acc_X', None), getattr(ui, 'lineEdit_acc_X', None)),
                vel_widgets=(getattr(ui, 'label_vel_X', None), getattr(ui, 'lineEdit_vel_X', None))
            ),
            'Y': StageAxisSelector(
                'Y', ui.comboBox_Y, ui.comboBox_SourceY,
                accel_widgets=(getattr(ui, 'label_acc_Y', None), getattr(ui, 'lineEdit_acc_Y', None)),
                vel_widgets=(getattr(ui, 'label_vel_Y', None), getattr(ui, 'lineEdit_vel_Y', None))
            ),
            'Z': StageAxisSelector(
                'Z', ui.comboBox_Z, ui.comboBox_SourceZ,
                accel_widgets=(getattr(ui, 'label_acc_Z', None), getattr(ui, 'lineEdit_acc_Z', None)),
                vel_widgets=(getattr(ui, 'label_vel_Z', None), getattr(ui, 'lineEdit_vel_Z', None))
            ),
        }
        # Filter None from widget lists if any attribute was missing
        for ax in self.axes.values():
            ax.accel_widgets = [w for w in ax.accel_widgets if w is not None]
            ax.vel_widgets = [w for w in ax.vel_widgets if w is not None]
            ax._update_speed_visibility()

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

    def update_ids(self, devices):
        self._all_ids = []
        for dev in devices:
            if dev['type'] == 'KDC':
                self._all_ids.append(f"K{dev['serial']}")
            elif dev['type'] == 'BSM':
                channels = dev.get('channels', [0])
                if len(channels) == 1:
                    self._all_ids.append(f"B{dev['serial']}")
                else:
                    for ch in channels:
                        self._all_ids.append(f"{ch}B{dev['serial']}")
        for ax in self.axes.values():
            ax._all_ids = list(self._all_ids)
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
