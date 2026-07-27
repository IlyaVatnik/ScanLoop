import pywinauto, time

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

for menu_name in ["File", "View", "Help"]:
    print(f"\n=== {menu_name} menu ===")
    try:
        win.menu_select(menu_name)
        time.sleep(1)
        # Find all menu items that appeared
        items = win.descendants(control_type="MenuItem")
        for item in items:
            try:
                txt = item.window_text() or item.element_info.name or ""
                if txt and len(txt) > 1:
                    print(f"  {txt}")
            except:
                pass
        win.type_keys("{ESC}")
        time.sleep(0.3)
    except Exception as e:
        print(f"  Error: {e}")
        try:
            win.type_keys("{ESC}")
            time.sleep(0.3)
        except:
            pass
