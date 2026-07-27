import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=10)
win = app.window(title='Kinesis')

# Find ALL elements with "Move" text
print('=== Elements with Move ===')
for c in win.descendants():
    nm = (c.element_info.name or '')
    tx = (c.window_text() or '')
    ct = c.element_info.control_type
    rect = c.rectangle()
    if ('Move' in nm or 'Move' in tx) and rect.width() > 5:
        print(f'  {ct}: name="{nm}" text="{tx}" rect={rect}')

# Find ALL clickable elements
print('\n=== All Button/Pane/Custom ===')
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    rect = c.rectangle()
    if ct in ['Button', 'Pane', 'Custom'] and rect.width() > 30 and rect.height() > 20:
        if nm and 'Image' not in nm:
            print(f'  {ct}: "{nm}" at {rect}')
