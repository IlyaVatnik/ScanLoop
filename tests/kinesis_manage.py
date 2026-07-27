import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Click "Manage"
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == "Manage" and ct == "Text":
        print(f"Clicking Manage...")
        c.click_input()
        time.sleep(3)
        break

# Check for new windows/dialogs
print("=== All windows ===")
try:
    all_wins = pywinauto.Desktop(backend='uia').windows()
    for w in all_wins:
        txt = w.window_text() or ''
        if txt:
            print(f"  Window: '{txt}'")
except Exception as e:
    print(f"Desktop error: {e}")

# Check main window children
print("\n=== Main window new elements ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    if nm and ct in ['Window', 'Pane', 'Button', 'Text', 'TreeItem', 'DataItem', 'ListItem', 'Edit', 'ComboBox']:
        print(f"  {ct}: '{nm}'")
