# АсфальтУчёт — Инструкция по установке и запуску

## Структура проекта

```
asfalt_backend/
├── app/
│   ├── main.py          ← главный файл FastAPI
│   ├── database.py      ← подключение к PostgreSQL
│   ├── models.py        ← таблицы базы данных
│   ├── schemas.py       ← валидация данных
│   └── routers/
│       ├── prikhod.py        ← API прихода сырья
│       ├── raskhod.py        ← API расхода сырья
│       ├── proizvodstvo.py   ← API производства
│       ├── prodazhi.py       ← API продаж
│       ├── sklad.py          ← API склада и справочников
│       └── dashboard.py      ← API дашборда
├── vesy_reader.py       ← чтение данных с весов (COM/USB)
├── requirements.txt
└── README.md
```

---

## Шаг 1 — Установка Python

Скачать Python 3.11: https://www.python.org/downloads/
При установке поставить галочку "Add to PATH"

---

## Шаг 2 — Установка PostgreSQL

Скачать: https://www.postgresql.org/download/
После установки открыть pgAdmin и создать базу:

```sql
CREATE USER asfalt_user WITH PASSWORD 'asfalt_pass';
CREATE DATABASE asfalt_db OWNER asfalt_user;
GRANT ALL PRIVILEGES ON DATABASE asfalt_db TO asfalt_user;
```

---

## Шаг 3 — Установка зависимостей

Открыть папку проекта в терминале:

```bash
cd asfalt_backend
pip install -r requirements.txt
```

---

## Шаг 4 — Переменные окружения

Создать файл `.env` в папке проекта:

```
DATABASE_URL=postgresql://asfalt_user:asfalt_pass@localhost:5432/asfalt_db
COM_PORT=COM3
BAUD_RATE=9600
```

---

## Шаг 5 — Запуск сервера

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Сервер запущен! Открыть в браузере:
- API документация: http://localhost:8000/docs
- Тест соединения:  http://localhost:8000/

---

## Шаг 6 — Запуск чтения весов

В отдельном окне терминала:

```bash
python vesy_reader.py
```

---

## Шаг 7 — Заполнение справочников (первый запуск)

Через документацию API (http://localhost:8000/docs) добавить:

1. Виды сырья (POST /api/sklad/vidy-syrya)
2. Поставщики
3. Покупатели
4. Марки асфальта
5. Автомобили

---

## API эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | /api/prikhod/ | Добавить приход сырья |
| GET  | /api/prikhod/ | Список приходов |
| GET  | /api/prikhod/itog-za-den | Итог прихода за день |
| POST | /api/raskhod/ | Добавить расход сырья |
| GET  | /api/raskhod/itog-za-den | Итог расхода за день |
| POST | /api/proizvodstvo/ | Добавить партию асфальта |
| GET  | /api/proizvodstvo/itog-za-den | Итог производства |
| POST | /api/prodazhi/ | Добавить отгрузку |
| GET  | /api/prodazhi/po-pokupatelam | Отчёт по покупателям |
| GET  | /api/prodazhi/avto/{nomer} | Найти авто по номеру |
| GET  | /api/sklad/ostatki | Остатки сырья |
| GET  | /api/dashboard/segodnya | Все данные дашборда |

---

## Подключение HTML-сайта к API

В файле `asfalt_zavod.html` добавить загрузку данных:

```javascript
async function loadDashboard() {
  const res = await fetch('http://localhost:8000/api/dashboard/segodnya');
  const data = await res.json();
  // заполнить цифры на дашборде
  document.getElementById('prikhod-kg').textContent = data.prikhod.itogo_kg;
  document.getElementById('vyruchka').textContent = data.prodazhi.vyruchka;
  // и т.д.
}
loadDashboard();
setInterval(loadDashboard, 30000); // обновлять каждые 30 секунд
```

---

## На сервере (для доступа директора с телефона)

Установить на любой компьютер в сети завода.
Директор открывает: http://192.168.1.X:8000/docs

Для интернет-доступа: арендовать VPS (5$/месяц) и развернуть там.
