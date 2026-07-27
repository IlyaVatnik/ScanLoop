import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Click Settings button to re-open
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

# Find settings window
settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        if 'Settings' in nm or 'Actuator' in nm:
            settings_win = c
            try:
                c.maximize()
                time.sleep(1)
            except:
                pass
            break

if not settings_win:
    print("Settings not found!")
    sys.exit(1)

# Click "Current" tab
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'TabItem':
        nm = (c.element_info.name or '')
        if nm == 'Current':
            c.click_input()
            time.sleep(2)
            print("Clicked Current tab")
            break

# Dump Current tab elements - look for Power values
print("\n=== Current tab content ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    tx = (c.window_text() or '')[:100]
    rect = c.rectangle()
    # Show elements in the upper part (Current tab content area)
    if ct in ['Text', 'Edit', 'CheckBox', 'Group'] and rect.top > 300 and rect.top < 880:
        if nm or tx:
            print(f"  {ct}: name='{nm}' text='{tx}' rect={rect}")

# Close without saving
print("\nClosing Settings (Cancel)...")
for c in settings_win.descendants():
    if c.element_info.control_type == 'Button' and c.element_info.name == 'Cancel':
        c.click_input()
        time.sleep(2)
        break
