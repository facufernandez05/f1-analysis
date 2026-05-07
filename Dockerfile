FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["sh", "/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
