import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Close and restart with proper selection
# First, find the device dropdown/selection area
print("=== Select device area ===")
for c in win.descendants():
    nm = (c.element_info.name or '')[:100]
    ct = c.element_info.control_type
    if ct == 'Text' and ('Select' in nm or '7086' in nm):
        rect = c.rectangle()
        print(f"  {ct}: '{nm}' at rect={rect}")

# Try clicking on "Select Device" text to see dropdown
for c in win.descendants():
    nm = (c.element_info.name or '')
    if nm == 'Select Device' and c.element_info.control_type == 'Text':
        rect = c.rectangle()
        # Click slightly to the right to open dropdown
        print(f"\nClicking Select Device area...")
        c.click_input()
        time.sleep(2)
        
        # Check for dropdown items
        for c2 in win.descendants():
            nm2 = (c2.element_info.name or '')
            ct2 = c2.element_info.control_type
            if ct2 == 'ListItem' and '7086' in nm2:
                print(f"  ListItem: {nm2}")
            if ct2 == 'ComboBox':
                print(f"  ComboBox: {nm2} text='{c2.window_text() or ''}'")
        break

# Also check all ListItems
print("\n=== All ListItems ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'ListItem' and nm:
        print(f"  {nm}")
