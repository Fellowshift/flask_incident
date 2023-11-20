FROM python:3.11

# Обновляем pip и устанавливаем poetry
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir poetry

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только файлы, необходимые для установки зависимостей.
COPY pyproject.toml poetry.lock* /app/

# Добавляем файл .env
COPY .env /app/

# Устанавливаем зависимости...
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

# Теперь копируем остальной проект
COPY . /app

# Настройка переменных среды
ENV FLASK_APP=main3.py
ENV FLASK_RUN_HOST=0.0.0.0

# Открываем порт 5000
EXPOSE 5000

# Запускаем приложение с помощью gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main3:app"]
