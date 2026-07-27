import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=10)
win = app.window(title='Kinesis')

# Find Move buttons
move_buttons = []
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'Button' and nm == 'Move':
        rect = c.rectangle()
        move_buttons.append((c, rect))

print(f'Found {len(move_buttons)} Move buttons')
for i, (btn, rect) in enumerate(move_buttons):
    print(f'  #{i}: {rect}')

if move_buttons:
    btn, rect = move_buttons[0]
    print(f'\nClicking Move #0 at {rect}...')
    btn.click_input()
    time.sleep(5)
    
    # Read positions
    print('\nAfter Move:')
    for c in win.descendants():
        nm = (c.element_info.name or '')
        if 'mm' in nm and len(nm) < 20:
            print(f'  {nm}')
