FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod -R 755 /app
USER 1000
CMD ["python", "consumer.py"]
