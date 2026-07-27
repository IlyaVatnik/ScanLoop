import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Close settings dialog
try:
    for c in win.descendants():
        if c.element_info.control_type == "Window" and "Settings" in (c.element_info.name or ''):
            print(f"Found settings window: {c.element_info.name}")
            # Click Cancel
            for btn in c.descendants():
                if btn.element_info.control_type == "Button" and btn.element_info.name == "Cancel":
                    btn.click_input()
                    print("Clicked Cancel")
                    time.sleep(1)
                    break
            break
except Exception as e:
    print(f"Close error: {e}")

time.sleep(1)

# Check if simulation
for c in win.descendants():
    nm = (c.element_info.name or '')
    if "Simulation" in nm or "simulation" in nm:
        print(f"SIMULATION detected: {nm}")

# The issue: "Simulation" mode. Need to check if device is really connected.
# Close TestClient and open Kinesis GUI instead (it handles USB properly)
print("\nClosing TestClient...")
# Find menu File -> Exit or just close
for c in win.descendants():
    if c.element_info.control_type == "MenuItem" and c.element_info.name == "File":
        c.click_input()
        time.sleep(0.5)
        break

# Try to find Exit in menu
for c in win.descendants():
    if c.element_info.control_type == "MenuItem" and "Exit" in (c.element_info.name or ''):
        c.click_input()
        print("Clicked Exit")
        break
