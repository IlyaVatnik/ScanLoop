import subprocess, time, sys, pywinauto
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Kill lingering
subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.TestClient.exe'], capture_output=True)
time.sleep(3)

# Launch TestClient
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
    print("NO SETTINGS!")
    sys.exit(1)

# Find Advanced tab by clicking ALL tab items and checking text
print("Looking for Advanced tab...")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'TabItem':
        rect = c.rectangle()
        # Find child text of this tab
        for child in c.descendants():
            if child.element_info.control_type == 'Text':
                txt = (child.window_text() or '')
                if 'Advanced' in txt:
                    print(f"  Found Advanced tab at {rect}, clicking...")
                    c.click_input()
                    time.sleep(2)
                    break
        # Also check if the TabItem itself has 'Advanced' in its accessible name
        nm = (c.element_info.name or '')
        if 'Advanced' in nm:
            print(f"  Found Advanced tab by name: {nm}")
            c.click_input()
            time.sleep(2)

# Now dump all elements in the Power section
print("\n=== Power section elements ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    tx = (c.window_text() or '')[:100]
    rect = c.rectangle()
    if ct in ['ComboBox', 'Text', 'CheckBox'] and rect.top > 470 and rect.top < 600 and rect.left > 250:
        if any(kw in (nm + tx).lower() for kw in ['power', 'rest', 'move', '6%', '%', 'combo']):
            print(f"  {ct}: name='{nm}' text='{tx}' rect={rect}")

# Find ALL ComboBoxes in the dialog
print("\n=== ALL ComboBoxes ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'ComboBox':
        rect = c.rectangle()
        txt = c.window_text() or ''
        print(f"  ComboBox at {rect}: text='{txt}'")
