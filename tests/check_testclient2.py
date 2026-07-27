import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')
print('=== Relevant elements ===')
for c in win.descendants():
    nm = (c.element_info.name or '')[:100]
    ct = c.element_info.control_type
    if nm and ct in ['Text', 'Button', 'TabItem', 'CheckBox', 'Edit', 'ListItem', 'Pane', 'Group']:
        if any(kw in nm.lower() for kw in ['simul', '7086', 'stepper', 'benchtop', 'power', 'channel', 'position', 'setting', 'command', 'error', 'status', 'voltage', 'loaded', 'init']):
            print(f'  {ct}: "{nm}"')
