import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Check for any tree items, device panels, or BSC202 references
print("=== Checking for devices after 25s wait ===")
found = False
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if '7086' in nm or 'BSC' in nm or 'Stepper' in nm or 'Benchtop' in nm:
        print(f"  FOUND: {ct}: '{nm}'")
        found = True
    if ct == 'TreeItem':
        print(f"  TreeItem: '{nm}'")
        found = True

if not found:
    print("  No devices found in tree")
    # Check event log for more info
    print("\n=== Event log ===")
    for c in win.descendants():
        ct = c.element_info.control_type
        nm = (c.element_info.name or '')
        tx = (c.window_text() or '')
        if 'thorlabs' in nm.lower() or 'usb' in nm.lower() or 'device' in nm.lower() or 'error' in nm.lower() or 'found' in nm.lower() or 'connect' in nm.lower():
            if ct == 'Text' and len(nm) > 3:
                print(f"  {ct}: '{nm}'")
