FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-vision.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt -r requirements-vision.txt
COPY app ./app
RUN useradd --create-home app && mkdir /data && chown app /data
USER app
ENV DATA_DIR=/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
