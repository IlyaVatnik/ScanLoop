import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=10)
win = app.window(title='Kinesis')

# Find TreeItems (device tree)
print('=== TreeItems ===')
for c in win.descendants():
    ct = c.element_info.control_type
    if ct == 'TreeItem':
        nm = (c.element_info.name or '')[:80]
        rect = c.rectangle()
        print(f'  TreeItem: "{nm}" at {rect}')

# Try clicking on 70864299-1 in the tree
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'TreeItem' and '70864299' in nm:
        print(f'\nDouble-clicking {nm}...')
        c.double_click_input()
        time.sleep(3)
        break

# Check if simulation changed
for c in win.descendants():
    nm = (c.element_info.name or '')
    if nm == 'Simulation':
        print(f'Simulation still present')
        break
else:
    print('No Simulation! Device connected!')
