# Лабораторная работа №3

Вариант 19. Веб-приложение на Flask умножает изображение на периодическую функцию `sin` или `cos`. Горизонтальная и вертикальная координаты входят в аргумент функции как сумма нормированных на период смещений.

## Структура

- `app.py` — Flask-приложение и функции обработки.
- `templates/index.html` — форма и таблица результатов.
- `static/style.css` — стили интерфейса.
- `tests/test_site.py` — pytest-тесты.
- `requirements.txt` — зависимости Python.
- `render.yaml`, `Procfile` — настройки PaaS/WSGI-сервера.
- `.github/workflows/ci.yml` — CI на GitHub Actions.
- `EXPLANATION.md` — подробный разбор проекта.

## Локальный запуск

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Откройте `http://127.0.0.1:5000`.

Для капчи задайте переменные среды:

```powershell
$env:RECAPTCHA_SITE_KEY="ваш-публичный-ключ"
$env:RECAPTCHA_SECRET_KEY="ваш-секретный-ключ"
python app.py
```

Если ключи не заданы, приложение запускается в режиме разработки и пропускает проверку капчи с поясняющим сообщением в коде. На PaaS ключи должны быть настроены, иначе защита не активна.

## Тесты

```powershell
python -m pytest -q
```

Покрыты обработка изображения, гистограмма, диапазон периода и неразрешенное расширение файла, а также Flask-маршрут.

## Деплой на Render

1. Создайте репозиторий GitHub и загрузите проект:

```powershell
git init
git add .
git commit -m "Lab 3 Flask app"
git branch -M main
git remote add origin https://github.com/<login>/<repo>.git
git push -u origin main
```

2. В Render выберите `New` → `Blueprint` и укажите репозиторий.
3. Render прочитает `render.yaml`.
4. В настройках сервиса задайте `RECAPTCHA_SITE_KEY` и `RECAPTCHA_SECRET_KEY`.
5. Render выполнит `pip install -r requirements.txt` и запустит `gunicorn app:app`.

Альтернативно создайте Web Service вручную: Runtime `Python`, build `pip install -r requirements.txt`, start `gunicorn app:app`.

## Нейронная сеть

Для варианта 19 нейронная сеть не является обязательным вычислительным методом: изображение преобразуется детерминированно по математической формуле. В интерфейсе явно указано, что классификация не включена, чтобы не выдавать заглушку за реальную нейросеть. Для реальной классификации можно позже добавить torchvision/ONNX, но это увеличит размер образа и время запуска в бесплатном PaaS-плане.
