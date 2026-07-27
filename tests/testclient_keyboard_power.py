import subprocess, time, sys, pywinauto
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.TestClient.exe'], capture_output=True)
time.sleep(3)

subprocess.Popen(r'C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.Kinesis.TestClient.exe')
time.sleep(15)

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=20)
win = app.window(title_re='.*TestClient.*')

# Uncheck startup, Initialize
for c in win.descendants():
    if c.element_info.control_type == "CheckBox" and "startup" in (c.element_info.name or '').lower():
        if c.get_toggle_state():
            c.click_input()
            time.sleep(0.3)

for c in win.descendants():
    if c.element_info.control_type == "Button" and c.element_info.name == "Initialize":
        c.click_input()
        time.sleep(15)
        break

# Click Settings
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
    print("No settings!")
    sys.exit(1)

# Click Advanced tab by text
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'Text' and (c.window_text() or '') == 'Advanced':
        rect = c.rectangle()
        # Click the parent TabItem
        for c2 in settings_win.descendants():
            if c2.element_info.control_type == 'TabItem':
                r2 = c2.rectangle()
                if r2.left <= rect.left and r2.right >= rect.right and r2.top <= rect.top and r2.bottom >= rect.top:
                    c2.click_input()
                    time.sleep(2)
                    print("Advanced tab clicked")
                    break
        break

# Now try to properly use the ComboBox for Resting Power
# ComboBox at approximately (239, 286)
print("\n=== Trying to set Resting Power ComboBox ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'ComboBox':
        rect = c.rectangle()
        if 235 < rect.left < 245 and 280 < rect.top < 300:
            print(f"Found ComboBox at {rect}")
            
            # Method 1: select by keyboard
            c.click_input()
            time.sleep(0.5)
            
            # Press Home to go to top of list
            pywinauto.keyboard.send_keys('{HOME}')
            time.sleep(0.3)
            
            # Press Down 6 times to reach 6%
            for i in range(6):
                pywinauto.keyboard.send_keys('{DOWN}')
                time.sleep(0.15)
            
            pywinauto.keyboard.send_keys('{ENTER}')
            time.sleep(1)
            
            print(f"  After: text='{c.window_text() or ''}'")
            break

# Same for Moving Power
print("\n=== Trying to set Moving Power ComboBox ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'ComboBox':
        rect = c.rectangle()
        if 235 < rect.left < 245 and 320 < rect.top < 340:
            print(f"Found ComboBox at {rect}")
            
            c.click_input()
            time.sleep(0.5)
            
            pywinauto.keyboard.send_keys('{HOME}')
            time.sleep(0.3)
            
            for i in range(6):
                pywinauto.keyboard.send_keys('{DOWN}')
                time.sleep(0.15)
            
            pywinauto.keyboard.send_keys('{ENTER}')
            time.sleep(1)
            
            print(f"  After: text='{c.window_text() or ''}'")
            break

# Check Persist
for c in settings_win.descendants():
    if c.element_info.control_type == 'CheckBox' and 'Persist' in (c.element_info.name or ''):
        state = c.get_toggle_state()
        if not state:
            c.click_input()
            time.sleep(0.3)
            print("\nPersist enabled")
        else:
            print("\nPersist already ON")
        break

# Click OK
print("\nClicking OK...")
for c in settings_win.descendants():
    if c.element_info.control_type == 'Button' and c.element_info.name == 'OK':
        c.click_input()
        time.sleep(5)
        break

# Check event log
print("\n=== Recent event log ===")
log_items = []
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if ct == 'Text' and ('Power' in nm or 'EEPROM' in nm or 'Settings Updated' in nm or 'Set Power' in nm):
        log_items.append(nm)
for item in log_items[-10:]:
    print(f"  {item}")
