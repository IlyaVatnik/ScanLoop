import subprocess, time, sys, pywinauto
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.TestClient.exe'], capture_output=True)
time.sleep(3)

subprocess.Popen(r'C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.Kinesis.TestClient.exe')
print("TestClient запущен, жду 15 сек...")
time.sleep(15)

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=20)
win = app.window(title_re='.*TestClient.*')

# Uncheck startup
for c in win.descendants():
    if c.element_info.control_type == "CheckBox" and "startup" in (c.element_info.name or '').lower():
        if c.get_toggle_state():
            c.click_input()
            time.sleep(0.3)

# Initialize
for c in win.descendants():
    if c.element_info.control_type == "Button" and c.element_info.name == "Initialize":
        c.click_input()
        time.sleep(15)
        print("Инициализация завершена!")

# Click Settings  
for c in win.descendants():
    nm = (c.element_info.name or '')
    ct = c.element_info.control_type
    if nm == 'Settings' and ct == 'Text':
        rect = c.rectangle()
        for c2 in win.descendants():
            if c2.element_info.control_type == 'Button':
                try:
                    r2 = c2.rectangle()
                    if r2.left <= rect.right and r2.right >= rect.left and r2.top <= rect.bottom + 20 and r2.bottom >= rect.top - 20:
                        c2.click_input()
                        time.sleep(4)
                        break
                except:
                    pass
        break

# Find ALL windows
print("\n=== Все окна ===")
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        rect = c.rectangle()
        print(f"  Window: '{nm}' at {rect}")

# Find settings
settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        rect = c.rectangle()
        # Settings window is typically large
        if rect.width() > 300 and rect.height() > 300:
            if 'Settings' in nm or 'Actuator' in nm or nm == '':
                settings_win = c
                print(f"\nFound settings: '{nm}' at {rect}")
                try:
                    c.maximize()
                    time.sleep(1)
                except:
                    pass
                break

if not settings_win:
    # Try finding by title
    try:
        settings_win = app.window(title='Actuator Settings')
        settings_win.maximize()
        time.sleep(1)
        print("Found by title: Actuator Settings")
    except:
        print("Settings window NOT FOUND!")
        print("Ждём ещё 5 сек...")
        time.sleep(5)
        # Try again
        for c in win.descendants():
            if c.element_info.control_type == 'Window':
                nm = c.element_info.name or ''
                rect = c.rectangle()
                print(f"  Window: '{nm}' at {rect}")

if settings_win:
    # Click Advanced tab
    for c in settings_win.descendants():
        ct = c.element_info.control_type
        if ct == 'TabItem':
            for child in c.descendants():
                if child.element_info.control_type == 'Text' and (child.window_text() or '') == 'Advanced':
                    c.click_input()
                    time.sleep(2)
                    print("\nВкладка Advanced открыта!")
                    break
        if ct == 'Text' and (c.window_text() or '') == 'Advanced':
            # Click the text itself
            c.click_input()
            time.sleep(2)
            break

    print("\n=== ГОТОВО ===")
    print("Теперь вы должны видеть окно Actuator Settings с вкладкой Advanced.")
    print("В левой части секция 'Power' с ComboBox'ами Resting Power и Moving Power.")
    print()
    print("ЧТО ДЕЛАТЬ:")
    print("1. ComboBox 'Resting Power' — кликните, выберите 6%")
    print("2. ComboBox 'Moving Power' — кликните, выберите 6%")
    print("3. Галочка 'Persist Settings to the Device' — включите")
    print("4. Нажмите OK")
    print()
    print("Когда сделаете — нажмите Enter в ЭТОЙ консоли.")
    input()
    print("Отлично! Закрываю TestClient...")
    subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.TestClient.exe'], capture_output=True)
    time.sleep(3)
    print("Готово!")
