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

# Check simulation
for c in win.descendants():
    nm = (c.element_info.name or '')
    if nm == 'IsSimulation':
        print("ВНИМАНИЕ: Simulation mode!")
        break
else:
    print("Реальное устройство подключено!")

# Click MOT_MOVE_RELATIVE in commands list
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'ListItem' and nm == 'MOT_MOVE_RELATIVE':
        c.click_input()
        time.sleep(1)
        print("Команда MOT_MOVE_RELATIVE выбрана!")
        break

print("\nTestClient готов к движению!")
print("На экране видна команда MOT_MOVE_RELATIVE.")
print("Channel = 1 (по умолчанию)")
print("Distance = 40 (40 мкм)")
print("Нажмите Send и проверьте двигается ли мотор!")
