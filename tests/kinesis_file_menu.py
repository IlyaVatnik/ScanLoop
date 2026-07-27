import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Close Manage Sequences dialog
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if ct == "Window" and "Manage" in nm:
        for btn in c.descendants():
            if btn.element_info.control_type == "Button" and btn.element_info.name == "Close":
                btn.click_input()
                print("Closed Manage dialog")
                time.sleep(1)
                break
        break

# Try File menu
print("\n=== File menu ===")
try:
    for c in win.descendants():
        ct = c.element_info.control_type
        nm = (c.element_info.name or '')
        if ct == "MenuItem" and nm == "File":
            c.click_input()
            time.sleep(1)
            break

    # Look at menu items
    for c in win.descendants():
        ct = c.element_info.control_type
        nm = (c.element_info.name or '')
        if ct == "MenuItem" and nm and nm not in ["File", "View", "Sequences", "Help", "_File", "_View", "_Sequences", "_Help", "Система"]:
            print(f"  MenuItem: '{nm}'")
except Exception as e:
    print(f"Error: {e}")

try:
    win.type_keys("{ESC}")
except:
    pass
time.sleep(0.5)

# Check Kinesis settings files
import os
kinesis_data = os.path.expanduser(r"~\AppData\Local\Thorlabs\Kinesis")
if os.path.exists(kinesis_data):
    print(f"\nKinesis data dir: {kinesis_data}")
    for f in os.listdir(kinesis_data):
        print(f"  {f}")
else:
    print(f"\nNo Kinesis data dir at {kinesis_data}")
    # Check other locations
    for path in [
        os.path.expanduser(r"~\AppData\Roaming\Thorlabs"),
        os.path.expanduser(r"~\Documents\Thorlabs"),
    ]:
        if os.path.exists(path):
            print(f"Found: {path}")
            for root, dirs, files in os.walk(path):
                for f in files[:10]:
                    print(f"  {os.path.join(root, f)}")
