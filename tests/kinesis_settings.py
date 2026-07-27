import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Find Settings buttons - there should be 2 (one per channel)
settings_buttons = []
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == "Settings" and ct == "Text":
        settings_buttons.append(c)

print(f"Found {len(settings_buttons)} Settings buttons")

if settings_buttons:
    # Click first Settings button (channel 1)
    print("Clicking Settings for channel 1...")
    settings_buttons[0].click_input()
    time.sleep(3)
    
    # Find Settings window
    print("\n=== Settings dialog ===")
    for c in win.descendants():
        ct = c.element_info.control_type
        nm = (c.element_info.name or '')[:100]
        tx = (c.window_text() or '')[:100]
        if (nm or tx) and ct in ['Window', 'TabItem', 'Text', 'Button', 'Group', 'Custom', 'Edit', 'CheckBox']:
            if 'Power' in nm or 'power' in nm or 'Rest' in nm or 'Move' in nm or 'Persist' in nm or 'Advanced' in nm or 'Tab' in ct:
                print(f"  {ct}: name='{nm}' text='{tx}'")
