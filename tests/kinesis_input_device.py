import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Click Input Device button
for c in win.descendants():
    if c.element_info.control_type == "Button" and c.element_info.name == "Input Device":
        print(f"Clicking Input Device button...")
        c.click_input()
        time.sleep(3)
        break

# Check what happened
print("=== After clicking Input Device ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    if nm and ct in ['Window', 'Pane', 'Custom', 'Button', 'Text', 'TreeItem', 'DataItem', 'ListItem', 'CheckBox']:
        print(f"  {ct}: '{nm}'")

# Check for new windows
print("\n=== All top-level windows ===")
try:
    wins = pywinauto.findwindows.find_elements(control_type="Window")
    for w in wins:
        if w.name:
            print(f"  Window: '{w.name}'")
except:
    pass
