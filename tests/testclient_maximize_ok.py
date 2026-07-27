import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Find ALL windows
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        rect = c.rectangle()
        print(f"Window: '{nm}' rect={rect}")

# Find Settings dialog - try both names
settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        if 'Settings' in nm or 'Actuator' in nm:
            settings_win = c
            # Maximize it
            try:
                c.maximize()
                time.sleep(1)
                print(f"Maximized: {c.rectangle()}")
            except:
                pass
            break

if not settings_win:
    # Try connecting to Actuator Settings as separate window
    try:
        settings_win = app.window(title='Actuator Settings')
        settings_win.maximize()
        time.sleep(1)
        print(f"Found by title: {settings_win.rectangle()}")
    except:
        print("Cannot find settings window")
        sys.exit(1)

# Click OK
for c in settings_win.descendants():
    if c.element_info.control_type == 'Button' and c.element_info.name == 'OK':
        print(f"Clicking OK at {c.rectangle()}")
        c.click_input()
        time.sleep(3)
        break

# Check if still open
still = False
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        if 'Settings' in nm or 'Actuator' in nm:
            still = True
            print(f"Still open: '{nm}' at {c.rectangle()}")
            break

if not still:
    print("Settings dialog closed!")
