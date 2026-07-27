import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Find Settings button/text and click it
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == "Settings":
        print(f"Found: {ct} - {nm}")
        print(f"  IsEnabled: {c.is_enabled()}")
        print(f"  IsVisible: {c.is_visible()}")
        c.click_input()
        print("Clicked Settings!")
        time.sleep(2)
        break

# Dump what appeared
print("\n=== After clicking Settings ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    tx = (c.window_text() or '')[:100]
    if nm or tx:
        print(f'  {ct}: name="{nm}" text="{tx}"')
