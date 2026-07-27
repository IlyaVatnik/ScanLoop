import pywinauto, time, sys
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
    print("No settings!")
    sys.exit(1)

# Advanced tab is already active (we can see Power section)
# Find "6%" text in the Power section area (Resting Power area: y around 300-430)
# Resting Power label at y=290, Moving Power at y=330

# The percentage list seems to be a scrollable view
# 0% at y=300, 1% at y=320, ..., 6% at y=420
# Let me try clicking 6% for Resting Power
print("=== Clicking 6% for Resting Power ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    rect = c.rectangle()
    if ct == 'Text' and nm == '6%' and rect.top > 400 and rect.top < 450:
        print(f"  Found 6% at {rect}")
        # Try different click methods
        c.click_input()
        time.sleep(1)
        print(f"  Clicked!")
        break

# Now check if there's a Moving Power "6%" - it should be nearby
# Moving Power label at y=330, but percentages start further down
# Actually, looking at the layout, the percentage list seems SHARED between Resting and Moving
# The percentages at y=300-900 are ALL for the Resting Power section
# Moving Power might have its own separate list or the same list serves both

# Let me check: are there TWO sets of percentages?
print("\n=== Checking for duplicate percentage texts ===")
counts = {}
for c in settings_win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'Text' and nm == '6%':
        rect = c.rectangle()
        print(f"  6% at {rect}")
        counts[rect.top] = nm

print(f"\nTotal 6% texts: {len(counts)}")

# Check if there's a separate Moving Power percentage area
# Maybe the ComboBoxes are OUTSIDE the Power section
print("\n=== ComboBoxes in full dialog ===")
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'ComboBox':
        rect = c.rectangle()
        txt = c.window_text() or ''
        print(f"  ComboBox at {rect}: text='{txt}'")
