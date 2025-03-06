FROM python:3.13-slim

WORKDIR /app
ENV PYTHONPATH /app

RUN apt-get update && apt-get install -y procps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "src.main"]
