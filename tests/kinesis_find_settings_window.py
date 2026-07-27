import pywinauto, time, sys
import pywinauto.mouse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Check all top-level windows in the desktop
desktop = pywinauto.Desktop(backend='uia')
print("=== ALL desktop windows ===")
for w in desktop.windows():
    txt = w.window_text() or ''
    if txt:
        print(f"  '{txt}'")

# Also check main Kinesis window
app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

# Look for any Window-type descendants (child windows / popups)
print("\n=== Child windows ===")
for c in win.descendants():
    ct = c.element_info.control_type
    if ct == 'Window':
        nm = (c.element_info.name or '')
        print(f"  Window: '{nm}'")

# Maybe the Settings button needs a proper click on the custom element
# Find the custom element with the gear icon
print("\n=== Custom elements near Settings ===")
settings_texts = []
for c in win.descendants():
    nm = (c.element_info.name or '')
    if nm == "Settings" and c.element_info.control_type == "Text":
        settings_texts.append(c)

for st in settings_texts:
    rect = st.rectangle()
    # Find the parent custom element
    print(f"\nSettings at {rect}")
    # Find custom/pane elements within 200px
    for c in win.descendants():
        ct = c.element_info.control_type
        if ct in ['Custom', 'Pane', 'Button']:
            try:
                r = c.rectangle()
                # Check overlap
                if r.left <= rect.right and r.right >= rect.left and r.top <= rect.bottom and r.bottom >= rect.top:
                    nm = (c.element_info.name or '')
                    print(f"  OVERLAPPING: {ct} '{nm}' rect={r}")
                    # Try clicking this element
                    print(f"  Clicking this element...")
                    c.click_input()
                    time.sleep(3)
                    
                    # Check for new window
                    for c2 in win.descendants():
                        if c2.element_info.control_type == 'Window':
                            nm2 = (c2.element_info.name or '')
                            print(f"  Window after click: '{nm2}'")
            except:
                pass
