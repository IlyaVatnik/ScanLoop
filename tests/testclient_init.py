import pywinauto, time

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')
controls = {c.element_info.name: c for c in win.descendants() if c.element_info.name}

# 1. Uncheck "Apply startup settings"
cb = controls.get("Apply startup settings")
if cb:
    # Find the checkbox (not the text)
    for c in win.descendants():
        if c.element_info.control_type == "CheckBox" and "startup" in (c.element_info.name or '').lower():
            state = c.get_toggle_state()
            print(f"Apply startup settings: checked={state}")
            if state:
                c.click_input()
                time.sleep(0.5)
                print("Unchecked!")
            break

# 2. Click on "70864299-1" to select device
dev = controls.get("70864299-1")
if dev:
    print(f"Found device: {dev.element_info.control_type}")
    dev.click_input()
    time.sleep(1)
    print("Selected device")

# 3. Click Initialize
init_btn = controls.get("Initialize")
if init_btn:
    print("Clicking Initialize...")
    init_btn.click_input()
    time.sleep(10)
    print("Done waiting")

# 4. Check output
print("\n=== After Init ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:100]
    if nm and ct in ["Text", "Button", "TabItem", "Pane", "Group"]:
        print(f'  {ct}: "{nm}"')

# 5. Dump output text
print("\n=== Output area ===")
for c in win.descendants():
    if c.element_info.control_type == "Text":
        txt = c.window_text()
        if txt and len(txt) > 2 and "startup" not in txt.lower() and "select" not in txt.lower():
            print(f'  "{txt}"')
