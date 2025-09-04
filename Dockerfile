FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-cache -r pyproject.toml

COPY ./app /app/app

EXPOSE ${INTERNAL_PORT}

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${INTERNAL_PORT}", "--reload"]
