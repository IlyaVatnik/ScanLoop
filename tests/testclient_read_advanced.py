import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Re-open Settings
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

# Find and maximize
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

# Click Advanced tab
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    rect = c.rectangle()
    if ct == 'TabItem' and 540 < rect.left < 650 and 450 < rect.top < 480:
        c.click_input()
        time.sleep(2)
        print("Clicked Advanced tab")
        break

# Check Power ComboBox values
print("\n=== Power section ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    nm = (c.element_info.name or '')
    if ct in ['Text', 'ComboBox'] and rect.top > 480 and rect.top < 600 and rect.left > 260 and rect.left < 600:
        tx = (c.window_text() or '')
        print(f"  {ct}: name='{nm}' text='{tx}' rect={rect}")

# Also try to get selection from combobox
for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'ComboBox' and rect.top > 510 and rect.top < 560 and rect.left > 460 and rect.left < 600:
        try:
            sel = c.selected_item()
            print(f"\nResting Power selected: {sel}")
        except Exception as e:
            print(f"\nResting Power select error: {e}")

for c in settings_win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'ComboBox' and rect.top > 550 and rect.top < 600 and rect.left > 460 and rect.left < 600:
        try:
            sel = c.selected_item()
            print(f"Moving Power selected: {sel}")
        except Exception as e:
            print(f"Moving Power select error: {e}")

# Cancel
for c in settings_win.descendants():
    if c.element_info.control_type == 'Button' and c.element_info.name == 'Cancel':
        c.click_input()
        time.sleep(1)
        break
