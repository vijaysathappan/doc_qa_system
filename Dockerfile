FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY model_cache/ /app/model_cache
COPY . .
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]