import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=10)
win = app.window(title='Kinesis')

# Find and click Move button for ch1 (the one near "70864299-1")
print('=== Looking for Move buttons ===')
move_buttons = []
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'Button' and nm == 'Move':
        rect = c.rectangle()
        print(f'  Move button at {rect}')
        move_buttons.append((c, rect))

# Click the first Move button (ch1)
if move_buttons:
    btn, rect = move_buttons[0]
    print(f'\nClicking first Move button at {rect}...')
    btn.click_input()
    time.sleep(5)
    
    # Check position after
    print('\n=== Position after Move ===')
    for c in win.descendants():
        nm = (c.element_info.name or '')
        if 'mm' in nm and len(nm) < 20 and ',' in nm:
            print(f'  {nm}')
    
    # Check log
    print('\n=== Last log entries ===')

import subprocess
log = r'C:\ProgramData\Thorlabs\MotionControl\Logs\Thorlabs.MotionControl.Kinesis.Log'
result = subprocess.run(['powershell', '-Command', f'Get-Content \"{log}\" -Tail 10'], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(result.stdout)
