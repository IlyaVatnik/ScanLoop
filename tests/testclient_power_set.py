import subprocess, time, sys, pywinauto
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Kill any lingering processes
subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.exe'], capture_output=True)
subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.TestClient.exe'], capture_output=True)
time.sleep(3)

# Launch TestClient
subprocess.Popen(r'C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.Kinesis.TestClient.exe')
time.sleep(15)

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=20)
win = app.window(title_re='.*TestClient.*')

# Uncheck startup settings
for c in win.descendants():
    if c.element_info.control_type == "CheckBox" and "startup" in (c.element_info.name or '').lower():
        if c.get_toggle_state():
            c.click_input()
            time.sleep(0.5)
            print("Unchecked startup settings")

# Click Initialize
for c in win.descendants():
    if c.element_info.control_type == "Button" and c.element_info.name == "Initialize":
        print("Clicking Initialize...")
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
print(f"Simulation: {sim}")

# Check position/status
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if ct == 'Text' and nm:
        if any(kw in nm for kw in ['Position', 'mm', 'Not Homed', 'Homed', 'Benchtop']):
            print(f"  {nm}")

# Click Settings button for channel 1
settings_clicked = False
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == 'Settings' and ct == 'Text':
        rect = c.rectangle()
        for c2 in win.descendants():
            if c2.element_info.control_type == 'Button':
                try:
                    r2 = c2.rectangle()
                    if r2.left <= rect.right and r2.right >= rect.left and r2.top <= rect.bottom + 20 and r2.bottom >= rect.top - 20:
                        c2.click_input()
                        time.sleep(4)
                        settings_clicked = True
                        print("Settings button clicked")
                        break
                except:
                    pass
        if settings_clicked:
            break

# Find settings window
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
    print("NO SETTINGS WINDOW!")
    sys.exit(1)

# Click Advanced tab
for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'TabItem' and 540 < rect.left < 660 and 440 < rect.top < 490:
        c.click_input()
        time.sleep(2)
        print("Advanced tab clicked")
        break

# Find Power ComboBoxes
power_combos = []
for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'ComboBox' and 460 < rect.left < 600 and 510 < rect.top < 600:
        power_combos.append((c, rect))
        print(f"  Power ComboBox at {rect}")

# For each combo, open dropdown and select 6%
for idx, (combo, rect) in enumerate(power_combos):
    label = "Resting" if idx == 0 else "Moving"
    print(f"\nSetting {label} Power to 6%...")
    
    # Click to open dropdown
    combo.click_input()
    time.sleep(1.5)
    
    # Find and click 6% using keyboard (type 6 then enter)
    # Or find the 6% text in the dropdown
    found = False
    for c in settings_win.descendants():
        nm = (c.element_info.name or '')
        ct = c.element_info.control_type
        if ct == 'Text' and nm == '6%':
            r = c.rectangle()
            # Make sure it's in the dropdown area
            if r.top > 500:
                c.click_input()
                time.sleep(1)
                found = True
                print(f"  Clicked 6% at {r}")
                break
    
    if not found:
        # Try keyboard: press '6' key
        combo.click_input()
        time.sleep(0.5)
        pywinauto.keyboard.send_keys('6')
        time.sleep(0.3)
        pywinauto.keyboard.send_keys('{ENTER}')
        time.sleep(1)
        print("  Used keyboard to type 6")

# Verify combo values
print("\n=== ComboBox values ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'ComboBox' and 460 < rect.left < 600 and 510 < rect.top < 600:
        txt = c.window_text() or ''
        print(f"  ComboBox at {rect}: text='{txt}'")

# Check Persist
print("\nChecking Persist...")
for c in settings_win.descendants():
    if c.element_info.control_type == 'CheckBox' and 'Persist' in (c.element_info.name or ''):
        state = c.get_toggle_state()
        if not state:
            c.click_input()
            time.sleep(0.5)
            print("  Persist enabled")
        else:
            print("  Persist already enabled")
        break

# Click OK
print("\nClicking OK...")
for c in settings_win.descendants():
    if c.element_info.control_type == 'Button' and c.element_info.name == 'OK':
        c.click_input()
        time.sleep(5)
        break

# Check dialog closed
still = False
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        if 'Settings' in nm or 'Actuator' in nm:
            still = True
            break
print(f"Settings dialog still open: {still}")

# Check event log
print("\n=== Event log ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    if 'Power' in nm or 'EEPROM' in nm or 'MOT_' in nm:
        print(f"  {nm}")
