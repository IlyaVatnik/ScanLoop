import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=10)
win = app.window(title='Kinesis')

print('=== Interactive elements ===')
seen = set()
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:80]
    key = f'{ct}:{nm}'
    if key not in seen and nm:
        seen.add(key)
        if ct in ['Button', 'MenuItem', 'TabItem', 'Tree', 'TreeItem', 'Group', 'Hyperlink', 'Custom', 'ToolBar']:
            rect = c.rectangle()
            print(f'  {ct}: "{nm}" rect={rect}')
