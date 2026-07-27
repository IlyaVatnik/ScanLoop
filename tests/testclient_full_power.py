import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Kill any lingering processes
import subprocess
subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.exe'], capture_output=True)
subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.TestClient.exe'], capture_output=True)
time.sleep(5)

# Launch TestClient
subprocess.Popen(r'C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.Kinesis.TestClient.exe')
time.sleep(12)

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=15)
win = app.window(title_re='.*TestClient.*')

# Check startup checkbox
for c in win.descendants():
    if c.element_info.control_type == "CheckBox" and "startup" in (c.element_info.name or '').lower():
        if c.get_toggle_state():
            c.click_input()
            time.sleep(0.5)

# Click Initialize
for c in win.descendants():
    if c.element_info.control_type == "Button" and c.element_info.name == "Initialize":
        c.click_input()
        time.sleep(15)
        break

# Check simulation
sim = False
for c in win.descendants():
    nm = (c.element_info.name or '')
    if nm == 'IsSimulation':
        sim = True
        break

if sim:
    print("WARNING: Simulation mode!")
else:
    print("Real device connected")

# Click Settings button
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == 'Settings' and ct == 'Text':
        for c2 in win.descendants():
            if c2.element_info.control_type == 'Button':
                try:
                    r1 = c.rectangle()
                    r2 = c2.rectangle()
                    if r2.left <= r1.right and r2.right >= r1.left and r2.top <= r1.bottom + 20 and r2.bottom >= r1.top - 20:
                        c2.click_input()
                        time.sleep(4)
                        break
                except:
                    pass
        break

# Find and maximize settings
settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        if 'Settings' in nm or 'Actuator' in nm:
            settings_win = c
            c.maximize()
            time.sleep(1)
            break

if not settings_win:
    print("No settings dialog!")
    sys.exit(1)

# Click Advanced tab (5th tab, x around 540-620)
for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'TabItem' and 540 < rect.left < 650 and 450 < rect.top < 480:
        c.click_input()
        time.sleep(2)
        print("Advanced tab clicked")
        break

# Now read current Power ComboBox values
print("\n=== Power ComboBoxes ===")
power_combos = []
for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'ComboBox' and rect.top > 510 and rect.top < 600 and rect.left > 460 and rect.left < 600:
        print(f"  ComboBox at {rect}")
        power_combos.append((c, rect))

# For each power combo, try to read selection and set to 6%
for idx, (combo, rect) in enumerate(power_combos):
    label = "Resting" if idx == 0 else "Moving"
    print(f"\n=== {label} Power ===")
    
    # Try expand and get selected
    try:
        combo.expand()
        time.sleep(1)
        # Look for highlighted/selected item
        for item in combo.descendants():
            nm = item.element_info.name or ''
            if '6%' in nm:
                print(f"  Found 6% at {item.rectangle()}")
                # Check if it's selected
                try:
                    if hasattr(item, 'selection'):
                        print(f"  Selection state: {item.selection}")
                except:
                    pass
        combo.collapse()
    except Exception as e:
        print(f"  Expand error: {e}")

# Try clicking on 6% text directly for Resting Power
print("\n=== Setting Resting Power to 6% ===")
for c in settings_win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'Text' and nm == '6%' and 1380 < rect.top < 1410:  # Around resting power area
        print(f"Clicking 6% at {rect}")
        c.click_input()
        time.sleep(2)
        break

# Check values after
print("\n=== ComboBox values after ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'ComboBox' and rect.top > 510 and rect.top < 600 and rect.left > 460 and rect.left < 600:
        txt = c.window_text() or ''
        print(f"  ComboBox at {rect}: text='{txt}'")
