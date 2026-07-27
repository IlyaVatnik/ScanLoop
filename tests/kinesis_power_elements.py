import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Dump ALL elements with "Power", "Rest", "Persist", "Advanced", or any new Settings elements
print("=== All Settings-related elements ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:120]
    tx = (c.window_text() or '')[:120]
    if ct == 'Text' and nm:
        if any(kw in nm.lower() for kw in ['power', 'rest', 'persist', 'advanced', 'move%', 'settings', 'channel']):
            print(f"  {ct}: name='{nm}' text='{tx}'")
    elif ct in ['CheckBox', 'Edit', 'Group', 'TabItem'] and nm:
        print(f"  {ct}: name='{nm}' text='{tx}'")

# Also dump all Edit controls (might have power values)
print("\n=== All Edit controls ===")
for c in win.descendants():
    ct = c.element_info.control_type
    if ct == 'Edit':
        tx = (c.window_text() or '')[:50]
        nm = (c.element_info.name or '')[:50]
        print(f"  Edit: name='{nm}' text='{tx}'")

# Check all Text elements for power-related content
print("\n=== All texts with % or power ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    tx = (c.window_text() or '')[:100]
    if ct == 'Text' and ('%' in nm or '%' in tx or 'Power' in nm or 'power' in nm or 'Current' in nm or '6' == nm):
        print(f"  {ct}: name='{nm}' text='{tx}'")
