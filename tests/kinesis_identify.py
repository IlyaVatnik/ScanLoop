import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=10)
win = app.window(title='Kinesis')

# Try clicking Identify button
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'Button' and nm == 'Identify':
        print(f'Clicking Identify at {c.rectangle()}...')
        c.click_input()
        time.sleep(3)
        break

# Check for any popup or new state
print('\n=== Status after Identify ===')
for c in win.descendants():
    nm = (c.element_info.name or '')
    if nm and len(nm) < 60:
        if any(kw in nm for kw in ['Simulation', 'Connected', 'Error', 'Blink', 'LED']):
            print(f'  {nm}')

# Try right-clicking on device panel for context menu
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if ct == 'Text' and nm == '70864299-1':
        rect = c.rectangle()
        print(f'\nRight-clicking on 70864299-1 at {rect}...')
        c.click_input(button='right')
        time.sleep(2)
        
        # Check for context menu
        for c2 in win.descendants():
            ct2 = c2.element_info.control_type
            if ct2 == 'MenuItem':
                nm2 = (c2.element_info.name or '')
                r2 = c2.rectangle()
                if r2.width() > 10 and r2.height() > 10:
                    print(f'  Context menu: "{nm2}" at {r2}')
        break
