FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry
WORKDIR /app
RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-ansi --no-root
COPY . .
EXPOSE 8070

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8070"]