import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Select MOT_MOVE_RELATIVE
for c in win.descendants():
    if c.element_info.control_type == 'ListItem' and (c.element_info.name or '') == 'MOT_MOVE_RELATIVE':
        c.click_input()
        time.sleep(1)
        print("MOT_MOVE_RELATIVE selected")
        break

# Find distance edit and set to 40
for c in win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'Edit' and rect.top > 550:
        c.click_input()
        time.sleep(0.3)
        pywinauto.keyboard.send_keys('^a')
        time.sleep(0.1)
        pywinauto.keyboard.send_keys('40')
        time.sleep(0.3)
        print(f"Distance set: {c.window_text()}")
        break

# Click Send
for c in win.descendants():
    if c.element_info.control_type == 'Button' and (c.element_info.name or '') == 'Send':
        print("Clicking Send...")
        c.click_input()
        time.sleep(5)
        break

# Check event log for result
print("\n=== Event log after Send ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if ct == 'Text' and nm:
        if any(kw in nm for kw in ['MoveRelative', 'Tx:', 'Rx:', 'Invoke', 'Position', 'Error', 'error']):
            if len(nm) < 100:
                print(f"  {nm}")
