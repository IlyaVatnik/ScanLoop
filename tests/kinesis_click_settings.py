import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Find "Settings" text elements and get their coordinates
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == "Settings" and ct == "Text":
        rect = c.rectangle()
        print(f"Settings text at: left={rect.left} top={rect.top} right={rect.right} bottom={rect.bottom}")
        # Click below the text (where the button likely is)
        center_x = (rect.left + rect.right) // 2
        click_y = rect.bottom + 15  # click below
        print(f"  Clicking at ({center_x}, {click_y})")
        
        import pywinauto.mouse
        pywinauto.mouse.click(coords=(center_x, click_y))
        time.sleep(3)
        
        # Check if Settings dialog opened
        found_settings_window = False
        for c2 in win.descendants():
            ct2 = c2.element_info.control_type
            nm2 = (c2.element_info.name or '')
            if ct2 == 'Window' and 'Settings' in nm2:
                found_settings_window = True
                print(f"  Settings window found: {nm2}")
        
        if found_settings_window:
            break
        else:
            print("  No settings window, trying again...")
