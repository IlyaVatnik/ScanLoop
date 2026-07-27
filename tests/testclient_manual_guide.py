import subprocess, time, sys, pywinauto
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.TestClient.exe'], capture_output=True)
time.sleep(3)

subprocess.Popen(r'C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.Kinesis.TestClient.exe')
print("TestClient launched, waiting 15s...")
time.sleep(15)

app = pywinauto.Application(backend='uia').connect(title_re='.*TestClient.*', timeout=20)
win = app.window(title_re='.*TestClient.*')

# Uncheck startup, Initialize
for c in win.descendants():
    if c.element_info.control_type == "CheckBox" and "startup" in (c.element_info.name or '').lower():
        if c.get_toggle_state():
            c.click_input()
            time.sleep(0.3)

for c in win.descendants():
    if c.element_info.control_type == "Button" and c.element_info.name == "Initialize":
        c.click_input()
        time.sleep(15)
        print("Initialized!")

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
                        print("Settings opened!")
                        break
                except:
                    pass
        break

# Find and maximize settings
settings_win = None
for c in win.descendants():
    if c.element_info.control_type == 'Window':
        nm = c.element_info.name or ''
        if 'Settings' in nm or 'Actuator' in nm:
            settings_win = c
            c.maximize()
            time.sleep(1)
            break

# Click Advanced tab
for c in settings_win.descendants():
    ct = c.element_info.control_type
    if ct == 'TabItem':
        for child in c.descendants():
            if child.element_info.control_type == 'Text' and (child.window_text() or '') == 'Advanced':
                c.click_input()
                time.sleep(2)
                print("Advanced tab opened!")
                break

print("\n=== ГОТОВО ===")
print("Окно Settings -> Advanced открыто на экране.")
print("Вам нужно:")
print("1. В секции Power (левая часть) найти 'Resting Power' ComboBox")
print("2. Кликнуть на ComboBox и выбрать 6%")
print("3. Найти 'Moving Power' ComboBox и выбрать 6%")  
print("4. Поставить галочку 'Persist Settings to the Device'")
print("5. Нажать OK")
print("\nНажмите Enter в консоли когда сделаете...")
input()
