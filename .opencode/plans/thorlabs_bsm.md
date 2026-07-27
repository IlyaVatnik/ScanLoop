# Plan: ThorlabsBSM — отдельный класс для Benchtop Stepper Motor

## Формат comboBox

| Устройство | Каналов | Entry |
|---|---|---|
| KDC | — | `K27254353` |
| BSM | 1 | `B70864299` |
| BSM | >1 | `0B70864299`, `1B70864299`, `2B70864299` |

## Парсинг префиксов (в stages_manager и stage_panel_controller)

- `K27254353` → тип=KDC, serial=27254353
- `B70864299` → тип=BSM, serial=70864299, channel=0
- `0B70864299` → тип=BSM, serial=70864299, channel=0
- `1B70864299` → тип=BSM, serial=70864299, channel=1

## Файлы для изменения

| Файл | Что делать |
|---|---|
| `Hardware/Stages/Thorlabs/thorlabs_stages.py` | Переименовать `ThorlabsAxis`→`ThorlabsCube`; добавить `ThorlabsBSM`; обновить `get_thorlabs_serials()` |
| `Hardware/Stages/stages_manager.py` | Импортировать `ThorlabsBSM`; диспетчеризация по префиксу |
| `Windows_GUI/stage_panel_controller.py` | Парсинг K/B-префиксов; генерация entries для comboBox |

## 1. `thorlabs_stages.py`

### 1a. `ThorlabsAxis` → `ThorlabsCube`

- Переименовать класс
- Убрать весь BSM-код (axis_type=BSM ветки из `__init__`, `get_position`, `move_relative`, `move_home`, `close`)
- `__init__` принимает только `serial_no`
- Оставить `ThorlabsAxis` как алиас:
  ```python
  class ThorlabsAxis:
      def __new__(cls, *args, **kwargs):
          return ThorlabsCube(*args, **kwargs)
  ```

### 1b. `ThorlabsBSM` класс

```python
class ThorlabsBSM:
    ENCODER_STEP = 0.002   # µm/step
    TOLERANCE = 0.3        # µm

    def __init__(self, serial_no, channel=0):
        _add_kinesis_to_path()
        from Hardware.Stages.thorlabs_kinesis import benchtop_stepper_motor as bsm
        
        self.serial_no = c_char_p(bytes(serial_no, "utf-8"))
        self.channel = c_short(channel)
        self.milliseconds = c_int(100)
        self.bsm = bsm
        self.is_connected = False
        
        self.bsm.TLI_BuildDeviceList()
        time.sleep(0.1)
        err = self.bsm.SBC_Open(self.serial_no)
        time.sleep(0.1)
        if err == 0:
            logger.info(f"[Thorlabs.BSM] Подключено: {serial_no}, channel={channel}")
            self.bsm.SBC_SetBacklash(self.serial_no, self.channel, c_long(0))
            self.is_connected = True
        else:
            raise RuntimeError(f"Не удалось подключиться к BSM {serial_no}")

    def get_position(self):
        pos = int(self.bsm.SBC_GetPosition(self.serial_no, self.channel))
        return round(pos * self.ENCODER_STEP, 1)

    def move_relative(self, distance_mkm):
        steps = int(distance_mkm / self.ENCODER_STEP)
        logger.info(f"[Thorlabs.BSM] move_relative ch={self.channel.value}: "
                     f"{distance_mkm} µm = {steps} steps")
        self.bsm.SBC_StartPolling(self.serial_no, self.channel, self.milliseconds)
        self.bsm.SBC_ClearMessageQueue(self.serial_no, self.channel)
        time.sleep(0.1)
        self.bsm.SBC_SetMoveRelativeDistance(self.serial_no, self.channel, c_int(steps))
        self.bsm.SBC_MoveRelativeDistance(self.serial_no, self.channel)

        # wait-loop как в старом коде
        new_pos = self.get_position() + distance_mkm
        diff = 1000
        while abs(diff) > self.TOLERANCE:
            pos = self.get_position()
            diff = pos - new_pos
        self.bsm.SBC_StopPolling(self.serial_no, self.channel)
        logger.info(f"[Thorlabs.BSM] move_relative finished at {self.get_position()} µm")

    def move_home(self):
        logger.info(f"[Thorlabs.BSM] move_home ch={self.channel.value}")
        self.bsm.SBC_StartPolling(self.serial_no, self.channel, self.milliseconds)
        self.bsm.SBC_ClearMessageQueue(self.serial_no, self.channel)
        err = self.bsm.SBC_Home(self.serial_no, self.channel)
        time.sleep(0.2)
        if err == 0:
            while True:
                pos = int(self.bsm.SBC_GetPosition(self.serial_no, self.channel))
                time.sleep(1)
                if pos == 0:
                    logger.info("[Thorlabs.BSM] At home")
                    break
                else:
                    logger.info(f"[Thorlabs.BSM] Homing... {pos}")
        self.bsm.SBC_StopPolling(self.serial_no, self.channel)

    def close(self):
        self.bsm.SBC_Close(self.serial_no)
        logger.info(f"[Thorlabs.BSM] Closed: {self.serial_no.value.decode()}")

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
```

### 1c. `get_thorlabs_serials()` — возврат с типами

Сейчас `_scan_via()` возвращает `[str]`. Нужно возвращать `[{'serial': str, 'type': str}]`.

```python
def _scan_via(driver_module, label):
    """Возвращает список {'serial': ..., 'type': label}"""
    ...
    serials = [{'serial': s.strip(), 'type': label} for s in raw.split(',') if s.strip()]
    ...

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

    # Добавляем каналы для BSM
    for dev in all_devices:
        if dev['type'] == 'BSM':
            ser = c_char_p(bytes(dev['serial'], "utf-8"))
            try:
                bsm.TLI_BuildDeviceList()
                bsm.SBC_Open(ser)
                time.sleep(0.1)
                n = bsm.SBC_GetNumChannels(ser)
                bsm.SBC_Close(ser)
                dev['channels'] = list(range(n.value if hasattr(n, 'value') else n))
                logger.info(f"[Thorlabs] BSM {dev['serial']}: каналы {dev['channels']}")
            except Exception as e:
                logger.warning(f"[Thorlabs] Не удалось получить каналы BSM {dev['serial']}: {e}")
                dev['channels'] = [0]

    return all_devices
```

## 2. `stages_manager.py`

```python
try:
    from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsCube, ThorlabsBSM
except Exception as e:
    logger.warning(f"Не удалось загрузить модуль Thorlabs: {e}")
    ThorlabsCube = ThorlabsBSM = None
```

В `setup_stages()` после строки `if stage_type == 'THORLABS':`:

```python
if stage_type == 'THORLABS':
    raw = params.get('serial', '')
    if not raw:
        continue
    if 'B' in raw and raw[0].isdigit():
        # BSM с явным каналом: 0B70864299
        channel = int(raw[0])
        serial = raw[2:]  # B70864299 -> 70864299
        if ThorlabsBSM:
            self.axes[axis_key] = ThorlabsBSM(serial, channel)
    elif raw.startswith('B'):
        # BSM без канала: B70864299
        serial = raw[1:]
        if ThorlabsBSM:
            self.axes[axis_key] = ThorlabsBSM(serial, 0)
    elif raw.startswith('K'):
        serial = raw[1:]
        if ThorlabsCube:
            self.axes[axis_key] = ThorlabsCube(serial)
    else:
        # fallback: без префикса — KDC
        if ThorlabsCube:
            self.axes[axis_key] = ThorlabsCube(raw)
```

## 3. `stage_panel_controller.py`

`StageAxisSelector.update_sources()` — обновить формирование списка для comboBox.

Текущий кеш — `self.parent.available_ports` (список строк) + `self.parent.available_ids` (словарь). Для Thorlabs приходит список словарей от `get_thorlabs_serials()`.

Нужно:

```python
def update_sources(self, stage_type):
    self.source_combo.clear()
    if stage_type == 'THORLABS':
        devices = self.parent.get_thorlabs_devices()  # список словарей
        for dev in devices:
            if dev['type'] == 'KDC':
                self.source_combo.addItem(f"K{dev['serial']}")
            elif dev['type'] == 'BSM':
                if len(dev.get('channels', [0])) == 1:
                    self.source_combo.addItem(f"B{dev['serial']}")
                else:
                    for ch in dev['channels']:
                        self.source_combo.addItem(f"{ch}B{dev['serial']}")
```

Если `get_thorlabs_devices()` нет, читать из кеша где он сейчас хранится.

## 4. Build_exe

**Ничего не менять.** HIDDEN_IMPORTS уже включает `Hardware.Stages.thorlabs_kinesis`, COLLECT_MODULES — всю `Hardware`. PyInstaller подберёт новые классы.

## 5. Логирование

Везде через `logging.getLogger(__name__)`:
- Каждый вызов `get_position`, `move_relative`, `move_home`, `close`
- `__init__`: успех/ошибка подключения
- `get_thorlabs_serials`: найденные устройства и каналы

## 6. Порядок выполнения

1. Редактировать `thorlabs_stages.py`: переименовать, убрать BSM-код из Cube, написать ThorlabsBSM, обновить `_scan_via`/`get_thorlabs_serials`
2. Редактировать `stages_manager.py`: импорт и диспетчеризация
3. Редактировать `stage_panel_controller.py`: форматирование entries
4. Проверка: `python -c "from Hardware.Stages.Thorlabs.thorlabs_stages import ThorlabsBSM"` — без ошибок
5. Проверка: `python -c "from Hardware.Stages.stages_manager import Stages"` — без ошибок
