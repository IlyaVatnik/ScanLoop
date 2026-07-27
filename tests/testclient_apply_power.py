import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window' and 'Settings' in (c.element_info.name or ''):
        settings_win = c
        break

# Check combo box values - try getting selected items
print("=== Checking combo box states ===")
combos = []
for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'ComboBox' and rect.top > 510 and rect.top < 600 and rect.left > 460 and rect.left < 600:
        print(f"  ComboBox at {rect}")
        # Try select method
        try:
            sel = c.selected_item()
            print(f"    selected_item: {sel}")
        except:
            pass
        try:
            # Try expanding
            c.expand()
            time.sleep(0.5)
            for item in c.children():
                print(f"    child: {item.element_info.control_type} name='{item.element_info.name}'")
            c.collapse()
        except Exception as e:
            print(f"    expand error: {e}")
        combos.append(c)

# Click OK to apply
print("\nClicking OK...")
for c in settings_win.descendants():
    if c.element_info.control_type == 'Button' and c.element_info.name == 'OK':
        c.click_input()
        time.sleep(3)
        break

# Check if dialog closed
print("Settings dialog still present?")
for c in win.descendants():
    if c.element_info.control_type == 'Window' and 'Settings' in (c.element_info.name or ''):
        print("  Still open!")
        break
else:
    print("  Dialog closed - settings applied!")

# Check event log for power params
print("\n=== Event log after OK ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    if 'Power' in nm or 'EEPROM' in nm or 'power' in nm:
        print(f"  {c.element_info.control_type}: {nm}")
