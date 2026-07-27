import subprocess, time, sys, pywinauto
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        if 'Settings' in nm or 'Actuator' in nm:
            settings_win = c
            break

if not settings_win:
    print("No settings window")
    sys.exit(1)

# Dump ALL elements
print("=== ALL elements ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    tx = (c.window_text() or '')[:100]
    rect = c.rectangle()
    if ct in ['TabItem', 'Text', 'ComboBox', 'CheckBox', 'Edit', 'Button', 'Group', 'Custom']:
        if nm or tx or ct in ['TabItem', 'Group', 'Custom']:
            # Filter to elements within the dialog area
            if rect.top > 200 and rect.top < 900 and rect.left > 10 and rect.width() > 5:
                print(f"  {ct}: name='{nm}' text='{tx}' rect={rect}")
