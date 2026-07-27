import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Uncheck startup settings
for c in win.descendants():
    if c.element_info.control_type == "CheckBox" and "startup" in (c.element_info.name or '').lower():
        state = c.get_toggle_state()
        print(f"Startup settings: checked={state}")
        if state:
            c.click_input()
            time.sleep(0.5)

# Click Initialize
for c in win.descendants():
    if c.element_info.control_type == "Button" and c.element_info.name == "Initialize":
        print("Clicking Initialize...")
        c.click_input()
        time.sleep(10)
        break

# Check simulation status
print("\n=== After Init ===")
has_simulation = False
for c in win.descendants():
    nm = (c.element_info.name or '')
    if 'Simulation' in nm:
        has_simulation = True
        print(f"SIMULATION: {nm}")

if not has_simulation:
    print("NO SIMULATION - device is REAL!")

# Check device status
for c in win.descendants():
    nm = (c.element_info.name or '')[:100]
    ct = c.element_info.control_type
    if nm and ct in ['Text', 'Button']:
        if any(kw in nm for kw in ['Position', 'Settings', 'Home', 'Stop', 'Not Homed', 'Limit', 'Error', 'Benchtop', 'Stepper', 'mm/s', 'mm']):
            print(f"  {ct}: '{nm}'")
