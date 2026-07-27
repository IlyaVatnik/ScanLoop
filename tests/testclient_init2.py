import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Check all descendants
controls = {c.element_info.name: c for c in win.descendants() if c.element_info.name}

# Check if device is in dropdown
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if '7086' in nm or 'BSC' in nm or 'Stepper' in nm:
        print(f"Found device: {ct} - {nm}")

# Uncheck startup settings
for c in win.descendants():
    if c.element_info.control_type == "CheckBox" and "startup" in (c.element_info.name or '').lower():
        state = c.get_toggle_state()
        print(f"Startup settings: checked={state}")
        if state:
            c.click_input()
            time.sleep(0.5)
            print("Unchecked!")

# Initialize
for c in win.descendants():
    if c.element_info.control_type == "Button" and c.element_info.name == "Initialize":
        print("Clicking Initialize...")
        c.click_input()
        time.sleep(8)
        break

# Check output and controls after init
print("\n=== After Init ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    tx = (c.window_text() or '')[:100]
    if nm and ct in ['Text', 'Button', 'TabItem', 'Group', 'CheckBox', 'Edit', 'ListItem', 'Pane']:
        if 'Simulation' in nm or '7086' in nm or 'Stepper' in nm or 'Benchtop' in nm or 'Position' in nm or 'Settings' in nm or 'Power' in nm:
            print(f"  {ct}: name='{nm}' text='{tx}'")
