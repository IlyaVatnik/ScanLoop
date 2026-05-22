# Hardware/Scanner.py
import logging
from serial.tools import list_ports

def get_available_com_ports():
    """
    Просто возвращает список имен всех доступных COM-портов в системе.
    Например: ['COM4', 'COM5', 'COM6', 'COM15']
    """
    logging.info("--- Получение списка всех COM-портов ---")
    ports = list_ports.comports()
    port_names = [port.device for port in ports]
    logging.info(f"--- Найдены порты: {port_names} ---")
    
    # Сортируем для красоты и предсказуемости
    try:
        port_names.sort(key=lambda x: int(x[3:]))
    except (ValueError, IndexError):
        pass # Если имя порта нестандартное, просто не сортируем
        
    return port_names
