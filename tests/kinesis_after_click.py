import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# First, get baseline of all elements
baseline = set()
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm:
        baseline.add(f"{ct}:{nm}")

# Click Button near first Settings text (channel 1)
for c in win.descendants():
    ct = c.element_info.control_type
    if ct == 'Button':
        try:
            r = c.rectangle()
            # Button near first Settings text: (240,230)-(299,300)
            if abs(r.left - 240) < 10 and abs(r.top - 230) < 10:
                print(f"Clicking Settings button ch1: rect={r}")
                c.click_input()
                time.sleep(4)
                break
        except:
            pass

# Check what changed
print("\n=== NEW elements after click ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    key = f"{ct}:{nm}"
    if nm and key not in baseline:
        print(f"  NEW: {ct}: '{nm}'")

# Check for Power
print("\n=== Looking for Power ===")
for c in win.descendants():
    nm = (c.element_info.name or '')[:100]
    ct = c.element_info.control_type
    if 'Power' in nm or 'power' in nm or 'Rest' in nm or 'rest' in nm or 'Persist' in nm or 'Advanced' in nm:
        print(f"  {ct}: '{nm}'")
