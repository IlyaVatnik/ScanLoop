import pywinauto, time, sys
import pywinauto.mouse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Wait for device
time.sleep(5)

# Find device and double-click
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == '70864299-2' and ct == 'Text':
        rect = c.rectangle()
        print(f"Device panel at: {rect}")
        c.double_click_input()
        time.sleep(5)
        break

# Now find all clickable elements near "Settings" text
print("\n=== Looking for Settings clickable area ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == "Settings" and ct == "Text":
        rect = c.rectangle()
        print(f"Settings text: rect={rect}")
        
        # Look for elements overlapping with Settings text
        for c2 in win.descendants():
            ct2 = c2.element_info.control_type
            try:
                r2 = c2.rectangle()
                # Check if this element overlaps with or is near the Settings text
                if (abs(r2.left - rect.left) < 50 and abs(r2.top - rect.top) < 50) or \
                   (r2.left <= rect.left and r2.right >= rect.right and r2.top <= rect.top and r2.bottom >= rect.bottom):
                    nm2 = (c2.element_info.name or '')
                    print(f"  Nearby: {ct2} '{nm2}' rect={r2}")
            except:
                pass
        
        # Try clicking directly on the text
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        print(f"  Clicking center ({center_x}, {center_y})")
        pywinauto.mouse.click(coords=(center_x, center_y))
        time.sleep(3)
        
        # Check for settings window
        for c3 in win.descendants():
            ct3 = c3.element_info.control_type
            nm3 = (c3.element_info.name or '')
            if ct3 == 'Window' and ('Setting' in nm3 or 'setting' in nm3 or 'Actuator' in nm3):
                print(f"  SETTINGS WINDOW FOUND: {nm3}")
                break
        break
