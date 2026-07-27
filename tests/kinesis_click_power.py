import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Click "Set Power Parameters" text
for c in win.descendants():
    nm = (c.element_info.name or '')
    if nm == 'Set Power Parameters':
        print(f"Clicking 'Set Power Parameters'...")
        c.click_input()
        time.sleep(3)
        break

# Now dump everything
print("\n=== After clicking Set Power Parameters ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    tx = (c.window_text() or '')[:100]
    if nm and ct in ['Text', 'Edit', 'CheckBox', 'Button', 'Group', 'TabItem', 'ComboBox', 'Slider', 'Window', 'Pane']:
        if any(kw in nm.lower() for kw in ['power', 'rest', 'move', 'persist', 'channel', '%', 'apply', 'ok', 'save', 'close', 'cancel', '6']):
            print(f"  {ct}: name='{nm}' text='{tx}'")

# Also check ALL edit controls
print("\n=== All Edit controls ===")
for c in win.descendants():
    ct = c.element_info.control_type
    if ct == 'Edit':
        tx = (c.window_text() or '')
        nm = (c.element_info.name or '')
        print(f"  Edit: name='{nm}' text='{tx}'")

# Check ALL checkboxes
print("\n=== All CheckBoxes ===")
for c in win.descendants():
    ct = c.element_info.control_type
    if ct == 'CheckBox':
        nm = (c.element_info.name or '')
        print(f"  CheckBox: name='{nm}'")
