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

# Find the Power Group and dump all its descendants
print("=== Power Group descendants ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'Group' and nm == 'Power':
        for child in c.descendants():
            ct2 = child.element_info.control_type
            nm2 = (child.element_info.name or '')
            tx2 = (child.window_text() or '')
            rect2 = child.rectangle()
            try:
                # Try to get value
                val = child.value
                print(f"  {ct2}: name='{nm2}' text='{tx2}' rect={rect2} value={val}")
            except:
                print(f"  {ct2}: name='{nm2}' text='{tx2}' rect={rect2}")
        break

# Also find ALL Edit controls and Slider controls in settings
print("\n=== Edit + Slider in settings ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct in ['Edit', 'Slider', 'ScrollBar', 'Spinner']:
        rect = c.rectangle()
        nm = (c.element_info.name or '')
        tx = (c.window_text() or '')
        if rect.top > 480:
            print(f"  {ct}: name='{nm}' text='{tx}' rect={rect}")
