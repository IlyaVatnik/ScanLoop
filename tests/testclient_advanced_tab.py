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

if not settings_win:
    print("Settings dialog not found!")
    sys.exit(1)

# Click "Advanced" tab
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'TabItem':
        nm = (c.element_info.name or '')
        # Check by rect position - Advanced is the 5th tab (after Moves/Jogs, Calibration, Stage/Axis)
        rect = c.rectangle()
        if 540 < rect.left < 630 and 450 < rect.top < 480:
            print(f"Clicking Advanced tab at {rect}...")
            c.click_input()
            time.sleep(2)
            break

# Also try finding by name containing 'Advanced'
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'Text' and 'Advanced' in nm:
        print(f"Found Advanced text: {nm} rect={c.rectangle()}")
        # Click the parent tab
        break

# Now dump all elements in Advanced view
print("\n=== Advanced tab elements ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:120]
    tx = (c.window_text() or '')[:120]
    rect = c.rectangle()
    dr = settings_win.rectangle()
    if rect.left >= dr.left and rect.right <= dr.right + 50 and rect.top >= dr.top - 50:
        if any(kw in (nm + tx).lower() for kw in ['power', 'rest', 'move%', 'persist', 'voltage', 'limit']):
            print(f"  {ct}: name='{nm}' text='{tx}' rect={rect}")

# Also dump ALL text elements in advanced area
print("\n=== All Texts in settings (advanced area) ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'Text':
        rect = c.rectangle()
        nm = (c.element_info.name or '')[:120]
        # Show texts in the main content area (below tabs)
        if rect.top > 470 and rect.top < 900 and rect.left > 250:
            print(f"  Text: '{nm}' rect={rect}")
