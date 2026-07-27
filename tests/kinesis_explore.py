import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Check all descendants for tree items / device names
print("=== Looking for device tree ===")
found_devices = []
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    # Look for tree items, device names, serial numbers
    if '7086' in nm or 'BSC' in nm or 'Stepper' in nm or ct == 'TreeItem':
        print(f"  {ct}: '{nm}'")
        found_devices.append(c)

# Also look for any pane/panel that might contain devices
print("\n=== Looking for panels/panes ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct in ['Tree', 'Pane'] and nm:
        print(f"  {ct}: '{nm}'")

# Look for any ComboBox with device selection
print("\n=== ComboBoxes ===")
for c in win.descendants():
    ct = c.element_info.control_type
    if ct == 'ComboBox':
        print(f"  ComboBox: '{(c.element_info.name or '')}' text='{(c.window_text() or '')}'")
        for ch in c.children():
            print(f"    child: {ch.element_info.control_type} '{(ch.element_info.name or '')}'")
