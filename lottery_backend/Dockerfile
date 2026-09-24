FROM python:3.12-slim
WORKDIR /app
COPY lottery_backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY lottery_backend/app.py ./app.py
ENV LOTTERY_DB_PATH=/data/lottery.sqlite3
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:app"]
