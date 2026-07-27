import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=10)
win = app.window(title='Kinesis')

# Click "Move" text for ch1 at (391, 193)
print('Clicking Move tab for ch1...')
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    rect = c.rectangle()
    if ct == 'Text' and nm == 'Move' and rect.left < 500:
        c.click_input()
        time.sleep(2)
        print(f'Clicked at {rect}')
        break

# Now find elements in the Move view
print('\n=== Move view elements ===')
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:80]
    tx = (c.window_text() or '')[:80]
    rect = c.rectangle()
    if ct in ['Text', 'Edit', 'Button', 'ComboBox', 'Slider'] and rect.top > 220 and rect.top < 500:
        if nm or (ct in ['Edit', 'Button', 'ComboBox']):
            print(f'  {ct}: name="{nm}" text="{tx}" rect={rect}')
