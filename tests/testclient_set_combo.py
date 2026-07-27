import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        if 'Settings' in nm or 'Actuator' in nm:
            settings_win = c
            break

if not settings_win:
    print("No settings!")
    sys.exit(1)

# The ComboBox at (239, 286) is near Resting Power label at (133, 290)
# The ComboBox at (239, 326) is near Moving Power label at (132, 330)
# These MUST be the Power ComboBoxes!

combos = []
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'ComboBox':
        rect = c.rectangle()
        if 235 < rect.left < 245 and rect.top > 280 and rect.top < 340:
            combos.append((c, rect))
            print(f"Power ComboBox at {rect}")

# The percentage list (0%-100%) is the dropdown for these ComboBoxes
# Let me try clicking ComboBox to expand, then clicking 6%

for idx, (combo, rect) in enumerate(combos):
    label = "Resting" if idx == 0 else "Moving"
    print(f"\n=== Setting {label} Power ===")
    
    # Click ComboBox to open dropdown
    combo.click_input()
    time.sleep(1)
    
    # Now look for 6% text - it should be visible in dropdown
    for c in settings_win.descendants():
        ct = c.element_info.control_type
        nm = (c.element_info.name or '')
        if ct == 'Text' and nm == '6%':
            r = c.rectangle()
            print(f"  Found 6% at {r}")
            c.click_input()
            time.sleep(1)
            break
    
    # Check ComboBox text after
    print(f"  ComboBox text after: '{combo.window_text() or ''}'")

# Check all ComboBoxes now
print("\n=== All ComboBox values ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'ComboBox':
        rect = c.rectangle()
        txt = c.window_text() or ''
        if rect.top < 360:
            print(f"  ComboBox at {rect}: '{txt}'")

# Enable Persist
print("\n=== Setting Persist ===")
for c in settings_win.descendants():
    if c.element_info.control_type == 'CheckBox' and 'Persist' in (c.element_info.name or ''):
        state = c.get_toggle_state()
        if not state:
            c.click_input()
            time.sleep(0.3)
            print("  Persist enabled")
        else:
            print("  Persist already ON")
        break

# Click OK
print("\nClicking OK...")
for c in settings_win.descendants():
    if c.element_info.control_type == 'Button' and c.element_info.name == 'OK':
        c.click_input()
        time.sleep(5)
        break

# Check event log for confirmation
print("\n=== Recent event log ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    if 'Power' in nm or 'EEPROM' in nm or 'Set' in nm:
        ct = c.element_info.control_type
        if ct == 'Text':
            print(f"  {nm}")
