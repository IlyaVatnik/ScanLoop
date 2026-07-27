import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Select MOT_MOVE_RELATIVE if not already selected
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'ListItem' and nm == 'MOT_MOVE_RELATIVE':
        c.click_input()
        time.sleep(1)
        print("MOT_MOVE_RELATIVE selected")
        break

# Find the Channel and Distance controls
print("\n=== Move controls ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:80]
    tx = (c.window_text() or '')[:80]
    rect = c.rectangle()
    if ct in ['Edit', 'ComboBox', 'Button'] and rect.top > 500:
        if nm or tx:
            print(f"  {ct}: name='{nm}' text='{tx}' rect={rect}")

# Find Send button
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'Button' and nm == 'Send':
        print(f"\nFound Send button at {c.rectangle()}")
        c.click_input()
        time.sleep(3)
        print("Clicked Send!")
        break

# Check event log for move response
print("\n=== Recent log ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if ct == 'Text' and nm:
        if 'Position' in nm or 'Move' in nm or 'error' in nm.lower() or '0x' in nm:
            print(f"  {nm}")
