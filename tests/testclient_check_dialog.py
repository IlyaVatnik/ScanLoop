import pywinauto, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window' and 'Settings' in (c.element_info.name or ''):
        settings_win = c
        break

# Dump ALL elements - maybe there's an error dialog or confirmation
print("=== ALL elements in Settings ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    tx = (c.window_text() or '')[:100]
    rect = c.rectangle()
    dr = settings_win.rectangle()
    if rect.left >= dr.left - 20 and rect.right <= dr.right + 100 and rect.top >= dr.top - 20:
        if ct in ['Text', 'Button', 'Edit', 'CheckBox', 'Window', 'Pane', 'Group', 'TabItem', 'ComboBox', 'Hyperlink']:
            if nm or tx:
                print(f"  {ct}: name='{nm}' text='{tx}' rect={rect}")

# Check if Persist is still checked
for c in settings_win.descendants():
    if c.element_info.control_type == 'CheckBox' and 'Persist' in (c.element_info.name or ''):
        print(f"\nPersist: checked={c.get_toggle_state()}")
        break

# Look for any popup dialogs
print("\n=== All windows ===")
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        print(f"  Window: '{c.element_info.name}' rect={c.rectangle()}")
