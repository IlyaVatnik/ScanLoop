import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Click "New"
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == "New" and ct == "Text":
        print(f"Clicking New...")
        c.click_input()
        time.sleep(3)
        break

# Check for dialog
print("=== After New ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    tx = (c.window_text() or '')[:100]
    if (nm or tx) and ct in ['Window', 'Pane', 'Button', 'Text', 'TreeItem', 'DataItem', 'ListItem', 'CheckBox', 'ComboBox', 'Edit']:
        print(f"  {ct}: name='{nm}' text='{tx}'")
