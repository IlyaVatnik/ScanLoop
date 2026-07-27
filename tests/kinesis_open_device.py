import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Find and click the device panel to open it
print("=== Looking for device panel ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if '70864299' in nm and ct in ['Text', 'Button', 'Custom', 'Pane']:
        print(f"  {ct}: '{nm}'")

# Try double-clicking on the device name to open it
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == '70864299-2' and ct == 'Text':
        print(f"\nDouble-clicking device: {nm}")
        c.double_click_input()
        time.sleep(5)
        break

# Check what appeared
print("\n=== After opening device ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    tx = (c.window_text() or '')[:100]
    if (nm or tx) and ct in ['Text', 'Button', 'TabItem', 'CheckBox', 'Edit', 'Group', 'Custom']:
        if '7086' in nm or 'Channel' in nm or 'Settings' in nm or 'Power' in nm or 'Move' in nm or 'mm' in nm or 'Home' in nm or 'Stop' in nm or 'Not' in nm or 'Limit' in nm:
            print(f"  {ct}: name='{nm}' text='{tx}'")
