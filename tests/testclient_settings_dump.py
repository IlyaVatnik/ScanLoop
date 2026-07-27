import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Find the Settings dialog (Window type)
settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window' and 'Settings' in (c.element_info.name or ''):
        settings_win = c
        break

if not settings_win:
    print("Settings dialog not found!")
    sys.exit(1)

print(f"Settings dialog: {settings_win.element_info.name}")
print(f"  Rect: {settings_win.rectangle()}")

# Dump ALL elements in settings dialog
print("\n=== ALL elements in Settings dialog ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:120]
    tx = (c.window_text() or '')[:120]
    if nm or ct in ['Text', 'TabItem', 'Button', 'Edit', 'CheckBox', 'Slider', 'Group', 'ComboBox', 'Pane', 'RadioButton', 'Hyperlink', 'Image']:
        rect = c.rectangle()
        # Only show elements inside the dialog rect
        dr = settings_win.rectangle()
        if rect.left >= dr.left and rect.right <= dr.right + 50 and rect.top >= dr.top - 50:
            print(f"  {ct}: name='{nm}' text='{tx}' rect={rect}")
