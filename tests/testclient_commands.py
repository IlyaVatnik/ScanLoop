import pywinauto, time, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=10)
win = app.window(title_re='.*TestClient.*')

# Click on Commands tab
for c in win.descendants():
    if c.element_info.control_type == "TabItem" and "Command" in (c.element_info.name or ''):
        print(f"Found tab: {c.element_info.name}")
        c.click_input()
        time.sleep(1)
        break

# Dump the Commands pane
print("\n=== Commands Tab ===")
def dump(el, depth=0, maxd=6):
    if depth > maxd: return
    for c in el.children():
        try:
            ct = c.element_info.control_type
            nm = (c.element_info.name or '')[:80]
            tx = (c.window_text() or '')[:80]
            if nm or tx:
                print('  '*depth + f'{ct}: name="{nm}" text="{tx}"')
            if ct in ['Pane', 'Custom', 'Group', 'ToolBar', 'ComboBox', 'Tab', 'DataItem', 'Tree', 'TreeItem', 'Button', 'CheckBox', 'RadioButton', 'Edit', 'Slider']:
                dump(c, depth+1, maxd)
        except: pass

dump(win, maxd=7)
