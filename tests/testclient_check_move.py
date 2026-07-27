import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Read current position
print("=== Current positions ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    if 'mm' in nm and len(nm) < 20 and ',' in nm:
        print(f"  {nm}")

# Select MOT_MOVE_RELATIVE  
for c in win.descendants():
    if c.element_info.control_type == 'ListItem' and (c.element_info.name or '') == 'MOT_MOVE_RELATIVE':
        c.click_input()
        time.sleep(1)
        break

# Set distance = 40 (40um = 20 raw steps, but TestClient uses device units)
# In Kinesis TestClient, distance is in device units
# 40um = 20 steps * 2048 units/step = 40960 device units? No...
# Actually for this stage: 40um in device units?
# NRT100 has 100mm range with 10240000 counts
# 40um = 0.04mm = 0.04/100 * 10240000 = 4096 device units
# But let's just type 40 and see

# Set distance
for c in win.descendants():
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ct == 'Edit' and rect.top > 550:
        c.click_input()
        time.sleep(0.2)
        pywinauto.keyboard.send_keys('^a')
        time.sleep(0.1)
        pywinauto.keyboard.send_keys('40')
        time.sleep(0.2)
        print(f"Distance: {c.window_text()}")
        break

# Get all commands before send
before_log = []
for c in win.descendants():
    nm = (c.element_info.name or '')
    if nm and len(nm) > 3:
        before_log.append(nm)

# Click Send
for c in win.descendants():
    if c.element_info.control_type == 'Button' and (c.element_info.name or '') == 'Send':
        c.click_input()
        time.sleep(5)
        print("Send clicked, waiting 5s...")
        break

# Read position after
print("\n=== Position after move ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    if 'mm' in nm and len(nm) < 20 and ',' in nm:
        print(f"  {nm}")

# Check for new log entries
print("\n=== New log entries ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    if nm and len(nm) > 3:
        if nm not in before_log:
            print(f"  NEW: {nm}")
