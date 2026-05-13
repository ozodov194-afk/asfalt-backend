"""
Скрипт для чтения данных с электронных весов через COM/USB порт.
Запускается отдельно от основного сервера.
Отправляет данные весов в API.
"""
import serial
import requests
import time
import re
import os

# ─── НАСТРОЙКИ ────────────────────────────────────────────────
COM_PORT    = os.getenv("COM_PORT", "COM3")        # Windows: COM3, COM4...
                                                    # Linux:  /dev/ttyUSB0
BAUD_RATE   = int(os.getenv("BAUD_RATE", "9600"))  # скорость порта весов
API_URL     = os.getenv("API_URL", "http://localhost:8000")
INTERVAL_S  = 1  # проверяем весы каждую секунду

# ─── ТЕКУЩИЙ ВЕС ─────────────────────────────────────────────
current_weight_kg = 0.0

def parse_weight(raw_line: str) -> float | None:
    """
    Парсим строку от весов и возвращаем вес в кг.
    Формат зависит от марки весов — ниже примеры.
    Настрой под свои весы!
    """
    raw = raw_line.strip()

    # Пример 1: "   +18200.5 kg" (большинство весов)
    m = re.search(r'([+-]?\d+\.?\d*)\s*k?g', raw, re.IGNORECASE)
    if m:
        return abs(float(m.group(1)))

    # Пример 2: просто число "18200"
    m = re.search(r'^([+-]?\d+\.?\d*)$', raw)
    if m:
        return abs(float(m.group(1)))

    return None

def read_weight_loop():
    """Основной цикл чтения весов"""
    global current_weight_kg

    print(f"Подключаемся к весам: {COM_PORT} @ {BAUD_RATE} baud...")

    try:
        ser = serial.Serial(
            port=COM_PORT,
            baudrate=BAUD_RATE,
            timeout=2
        )
        print(f"✓ Весы подключены: {COM_PORT}")
    except Exception as e:
        print(f"✗ Ошибка подключения к весам: {e}")
        print("Запускаем в режиме симуляции (для тестирования)")
        simulate_weights()
        return

    while True:
        try:
            line = ser.readline().decode("ascii", errors="ignore")
            if line:
                weight = parse_weight(line)
                if weight is not None:
                    current_weight_kg = weight
                    print(f"Весы: {weight:.1f} кг")
        except Exception as e:
            print(f"Ошибка чтения: {e}")
        time.sleep(INTERVAL_S)

def get_current_weight() -> float:
    """Возвращает последний считанный вес — вызывается из API"""
    return current_weight_kg

def simulate_weights():
    """Симуляция весов для тестирования без реального оборудования"""
    import random
    weights = [28400, 0, 32600, 0, 18500, 0]  # брутто/тара попеременно
    i = 0
    while True:
        global current_weight_kg
        current_weight_kg = weights[i % len(weights)]
        print(f"[СИМУЛЯЦИЯ] Весы: {current_weight_kg} кг")
        i += 1
        time.sleep(5)

# ─── ЭНДПОИНТ ВЕСОВ (добавить в main.py) ─────────────────────
# Пример как фронтенд получает текущий вес:
#
# @app.get("/api/vesy/tekushiy-ves")
# def tekushiy_ves():
#     return {"ves_kg": get_current_weight()}

if __name__ == "__main__":
    read_weight_loop()
