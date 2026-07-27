import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Find and click "Input Device" button or similar
print("=== Looking for device add mechanisms ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm and ('device' in nm.lower() or 'input' in nm.lower() or 'add' in nm.lower() or 'scan' in nm.lower()):
        print(f"  {ct}: '{nm}'")

# Try File menu -> look for "Add Device" or "Connect"
print("\n=== Trying File menu ===")
try:
    win.menu_select("File")
    time.sleep(1)
    for c in win.descendants():
        ct = c.element_info.control_type
        nm = (c.element_info.name or '')
        tx = (c.window_text() or '')
        if ct == "MenuItem" and (nm or tx):
            print(f"  {ct}: name='{nm}' text='{tx}'")
except Exception as e:
    print(f"File menu error: {e}")

try:
    win.type_keys("{ESC}")
except:
    pass
time.sleep(0.5)

# Try right-click in the main area
print("\n=== Trying right-click in empty area ===")
try:
    # Click on the text "Move devices here to access full functionality"
    for c in win.descendants():
        if "Move devices" in (c.element_info.name or ''):
            print(f"Found: {c.element_info.name}")
            c.click_input(button='right')
            time.sleep(1)
            # Check context menu
            for c2 in win.descendants():
                ct2 = c2.element_info.control_type
                nm2 = (c2.element_info.name or '')
                if ct2 == "MenuItem" and nm2:
                    print(f"  Context: {nm2}")
            break
except Exception as e:
    print(f"Right-click error: {e}")
