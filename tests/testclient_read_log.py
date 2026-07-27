import subprocess, time, sys, pywinauto
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Get ALL event log items with their full text
print("=== FULL event log ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    tx = (c.window_text() or '')
    if ct == 'Text' and nm:
        if any(kw in nm for kw in ['Power', 'EEPROM', 'Setting', 'Parameter', 'rest', 'move', 'Persist']):
            print(f"  name='{nm}'")

# Also check the list items in the event log (might contain more detail)
print("\n=== Event log list items ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'ListItem':
        if any(kw in nm for kw in ['Power', 'EEPROM', 'Setting', 'Parameter']):
            print(f"  {nm}")

# Check if there's a status bar or message area
print("\n=== Status/message areas ===")
for c in win.descendants():
    ct = c.element_info.control_type
    tx = (c.window_text() or '')
    nm = (c.element_info.name or '')
    if ct == 'Text' and tx:
        if len(tx) > 5 and len(tx) < 200:
            if any(kw in tx.lower() for kw in ['power', 'rest', 'move', 'param', '6', 'eeprom']):
                print(f"  text='{tx}' name='{nm}'")
