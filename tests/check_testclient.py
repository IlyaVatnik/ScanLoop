import pywinauto, time, re

time.sleep(2)

# Try to find TestClient or Kinesis window
try:
    app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*|.*Kinesis.*', timeout=10)
    win = app.window(title_re='.*TestClient.*|.*Kinesis.*')
    print('Title:', win.window_text())
    print()
    for i, c in enumerate(win.children()):
        ctype = c.element_info.control_type
        txt = (c.window_text() or '')[:100]
        name = (c.element_info.name or '')[:100]
        if txt or name:
            print(f'[{i}] {ctype}: text="{txt}" name="{name}"')
except Exception as e:
    print(f"Error: {e}")
