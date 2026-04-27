FROM python:3.11-slim
WORKDIR /app
COPY examples/greenhouse_monitoring/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "examples.greenhouse_monitoring.app:app", "--host", "0.0.0.0", "--port", "3000"]
