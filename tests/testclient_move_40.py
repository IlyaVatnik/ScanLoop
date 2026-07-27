import subprocess, time, sys, pywinauto
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Kill everything
subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.exe'], capture_output=True)
subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.TestClient.exe'], capture_output=True)
time.sleep(5)

# Launch TestClient
subprocess.Popen(r'C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.Kinesis.TestClient.exe')
print("TestClient запущен, жду 15 сек...")
time.sleep(15)

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=20)
win = app.window(title_re='.*TestClient.*')

# Uncheck startup + Initialize
for c in win.descendants():
    if c.element_info.control_type == "CheckBox" and "startup" in (c.element_info.name or '').lower():
        if c.get_toggle_state():
            c.click_input()
            time.sleep(0.3)

for c in win.descendants():
    if c.element_info.control_type == "Button" and c.element_info.name == "Initialize":
        c.click_input()
        time.sleep(15)
        print("Initialized!")

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
    if ct == 'Edit' and rect.top > 550 and rect.top < 620:
        c.click_input()
        time.sleep(0.3)
        # Clear and type
        pywinauto.keyboard.send_keys('^a')
        time.sleep(0.1)
        pywinauto.keyboard.send_keys('40')
        time.sleep(0.3)
        print(f"Distance set to 40 at {rect}")
        break

# Click Send
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'Button' and nm == 'Send':
        c.click_input()
        time.sleep(5)
        print("Send clicked!")
        break

# Read result
print("\n=== Result ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if ct == 'Text' and nm:
        if any(kw in nm for kw in ['Position', 'mm', 'Move', 'Error', 'error', '0x']):
            if len(nm) < 50:
                print(f"  {nm}")
