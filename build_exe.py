# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 16:58:46 2026

@author: Александр
"""
# -*- coding: utf-8 -*-
"""
Скрипт для автоматической сборки проекта ScanLoop в .exe с визуализацией прогресса
"""
import os
import sys
import shutil
import subprocess

def main():
    print("=== НАЧАЛО СБОРКИ ПРОЕКТА ===")
    current_dir = os.getcwd()
    
    # 1. Очистка
    folders_to_clean = ['build', 'dist']
    for folder in folders_to_clean:
        path = os.path.join(current_dir, folder)
        if os.path.exists(path):
            print(f"Удаление старой папки {folder}...")
            shutil.rmtree(path)
            
    spec_file = os.path.join(current_dir, 'main.spec')
    if os.path.exists(spec_file):
        os.remove(spec_file)

    print("\nЗапуск PyInstaller. Начинаем компиляцию...\n" + "-"*50)
    
    standa_path = os.path.join("Hardware", "Stages", "Standa")
    lbtek_path  = os.path.join("Hardware", "Stages", "LBTEK", "LBTEKx64")

    # Формируем команду (если вы уже починили ошибку с графиками, раскомментируйте --windowed)
    command = [
        sys.executable, "-m", "PyInstaller", 
        "--onedir", 
        "--windowed", # <-- Раскомментируйте (уберите #), когда программа перестанет падать
        "--exclude-module", "PyQt6",
        "--exclude-module", "PySide6",
        f"--add-data={standa_path};Hardware/Stages/Standa",
        f"--add-data={lbtek_path};Hardware/Stages/LBTEK/LBTEKx64",
        "main.py"
    ]

    try:
        # Popen позволяет читать вывод программы прямо в процессе её работы
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, # Направляем ошибки в тот же поток
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace' # Защита от кракозябр в Windows
        )

        # Выводим каждую строчку, которую генерирует PyInstaller в реальном времени
        for line in process.stdout:
            print(line, end='')

        # Ждем завершения процесса
        process.wait()
        
        print("-" * 50)
        
        if process.returncode != 0:
            print("\nОШИБКА: Сборка прервалась! Смотрите логи выше.")
            return
            
        print("Компиляция кода завершена успешно!")
        
    except Exception as e:
        print(f"\nКритическая ошибка при запуске сборки: {e}")
        return

    # 3. Копирование внешних папок для данных
    print("\nСоздание папок для спектров и данных...")
    dist_main_dir = os.path.join(current_dir, 'dist', 'main')
    
    folders_to_copy = [
        'ProcessedData', 
        'SpectralData', 
        'SpectralBinData',
        'TimeDomainData'
    ]

    for folder in folders_to_copy:
        dst = os.path.join(dist_main_dir, folder)
        os.makedirs(dst, exist_ok=True)
        print(f" -> Создана папка {folder}")

    print("\n=== СБОРКА УСПЕШНО ЗАВЕРШЕНА! ===")
    print(f"Ваша готовая программа лежит здесь:\n{dist_main_dir}")

if __name__ == "__main__":
    main()