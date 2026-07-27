import subprocess, time, sys, pywinauto
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

subprocess.run(['taskkill', '/F', '/IM', 'Thorlabs.MotionControl.Kinesis.TestClient.exe'], capture_output=True)
time.sleep(3)

subprocess.Popen(r'C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.Kinesis.TestClient.exe')
print("TestClient запущен...")
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
sim = False
for c in win.descendants():
    nm = (c.element_info.name or '')
    if nm == 'IsSimulation':
        sim = True
        break
print(f"Simulation: {sim}")
if sim:
    print("ОШИБКА: Simulation mode! Устройство не реальное!")
    sys.exit(1)

# Now click on MOT_MOVE_RELATIVE in the commands list
print("\nИщем MOT_MOVE_RELATIVE в списке команд...")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')
    if ct == 'ListItem' and nm == 'MOT_MOVE_RELATIVE':
        print(f"  Found: {nm}")
        c.click_input()
        time.sleep(1)
        break

# Look for the move controls that appeared
print("\n=== Элементы управления Move ===")
for c in win.descendants():
    ct = c.element_info.control_type
    nm = (c.element_info.name or '')[:80]
    tx = (c.window_text() or '')[:80]
    rect = c.rectangle()
    if ct in ['Edit', 'Button', 'Text', 'ComboBox'] and nm:
        if 'move' in nm.lower() or 'distance' in nm.lower() or 'relative' in nm.lower() or 'channel' in nm.lower() or 'send' in nm.lower():
            print(f"  {ct}: name='{nm}' text='{tx}' rect={rect}")

print("\nТеперь вы должны видеть TestClient с командой MOT_MOVE_RELATIVE.")
print("Вам нужно:")
print("1. Убедиться что Channel выбран правильно (1 или 2)")
print("2. Ввести Distance = 40 (это 40 мкм)")
print("3. Нажать Send")
print("4. ПОСМОТРЕТЬ/ПОСЛУШАТЬ двигается ли мотор физически")
print()
print("Нажмите Enter когда проверите движение ch1...")
input()
