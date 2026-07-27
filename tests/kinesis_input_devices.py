import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# File -> Input Devices...
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == "MenuItem" and nm == "File":
        c.click_input()
        time.sleep(0.5)
        break

time.sleep(0.5)
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == "MenuItem" and "Input Devices" in nm:
        print(f"Clicking Input Devices...")
        c.click_input()
        time.sleep(3)
        break

# Check what opened
print("\n=== After Input Devices ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:120]
    tx = (c.window_text() or '')[:120]
    if (nm or tx) and ct in ['Window', 'Pane', 'Button', 'Text', 'TreeItem', 'DataItem', 'ListItem', 'Edit', 'ComboBox', 'CheckBox', 'Group']:
        print(f"  {ct}: name='{nm}' text='{tx}'")
