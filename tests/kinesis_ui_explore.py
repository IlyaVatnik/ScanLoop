import pywinauto, time, sys

app = pywinauto.Application(backend='uia').connect(title='Kinesis', timeout=15)
win = app.window(title='Kinesis')

def dump_children(parent, depth=0, max_depth=5):
    if depth > max_depth:
        return
    for c in parent.children():
        try:
            ctype = c.element_info.control_type
            name = (c.element_info.name or '')[:80]
            txt = (c.window_text() or '')[:80]
            auto_id = (c.element_info.automation_id or '')[:40]
            if name or txt:
                print('  ' * depth + f'{ctype}: name="{name}" text="{txt}" aid="{auto_id}"')
            if ctype in ['Tree', 'TreeItem', 'Pane', 'Custom', 'DataItem', 'ToolBar', 'MenuBar']:
                dump_children(c, depth + 1, max_depth)
        except Exception as e:
            pass

dump_children(win, max_depth=6)
