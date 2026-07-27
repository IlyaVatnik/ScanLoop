import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Find Settings dialog
settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window' and 'Settings' in (c.element_info.name or ''):
        settings_win = c
        break

if not settings_win:
    print("Settings dialog not found!")
    sys.exit(1)

# First check current values of the Power ComboBoxes
print("=== Power ComboBox current values ===")
power_combos = []
for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'ComboBox' and rect.top > 510 and rect.top < 600 and rect.left > 460:
        txt = c.window_text() or ''
        print(f"  ComboBox: text='{txt}' rect={rect}")
        power_combos.append(c)

print(f"\nFound {len(power_combos)} power ComboBoxes")

# Try to set first ComboBox (Resting Power) to 6%
# Click to open dropdown
if len(power_combos) >= 1:
    print("\n=== Setting Resting Power ===")
    combo = power_combos[0]
    combo.click_input()
    time.sleep(1)
    
    # Look for 6% in dropdown
    for c in settings_win.descendants():
        if c.element_info.control_type == 'Text' and (c.element_info.name or '') == '6%':
            print(f"Found '6%' at {c.rectangle()}")
            c.click_input()
            time.sleep(1)
            break
    
    print(f"After selection: text='{combo.window_text() or ''}'")

# Set second ComboBox (Moving Power) to 6%
if len(power_combos) >= 2:
    print("\n=== Setting Moving Power ===")
    combo2 = power_combos[1]
    combo2.click_input()
    time.sleep(1)
    
    for c in settings_win.descendants():
        if c.element_info.control_type == 'Text' and (c.element_info.name or '') == '6%':
            r = c.rectangle()
            if r.top > 550:  # Moving power area
                print(f"Found '6%' at {r}")
                c.click_input()
                time.sleep(1)
                break
    
    print(f"After selection: text='{combo2.window_text() or ''}'")

# Check "Persist Settings to the Device"
print("\n=== Setting Persist ===")
for c in settings_win.descendants():
    if c.element_info.control_type == 'CheckBox' and 'Persist' in (c.element_info.name or ''):
        state = c.get_toggle_state()
        print(f"Persist checkbox: checked={state}")
        if not state:
            c.click_input()
            time.sleep(0.5)
            print(f"Persist now: checked={c.get_toggle_state()}")
        break
