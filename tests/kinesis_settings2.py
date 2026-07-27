import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Find ALL Settings elements with full info
print("=== All 'Settings' elements ===")
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if 'Settings' in nm or 'settings' in nm:
        try:
            print(f"  {ct}: name='{nm}' enabled={c.is_enabled()} visible={c.is_visible()} clickable={c.is_clickable()}")
        except:
            print(f"  {ct}: name='{nm}'")

# Dump the channel area more carefully
print("\n=== Channel elements ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:80]
    if ct in ['Button', 'Hyperlink'] and nm:
        print(f"  {ct}: '{nm}'")
