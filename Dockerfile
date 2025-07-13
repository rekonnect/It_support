FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install netcat which is needed by our wait-for-it.sh script
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./wait-for-it.sh .
RUN chmod +x ./wait-for-it.sh

COPY . .

EXPOSE 8000

# The command is now in docker-compose.yml, so we just need a default.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
