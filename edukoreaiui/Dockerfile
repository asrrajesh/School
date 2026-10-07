FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# flet-web is an optional extra of flet; install it at build time so the
# container does not pip-install it at every cold start.
RUN pip install --no-cache-dir -r requirements.txt flet-web==0.86.5

COPY . .

# Flet reads FLET_SERVER_IP / FLET_SERVER_PORT from the environment, so
# main.py needs no container-specific code.
ENV PYTHONUNBUFFERED=1 \
    UI_MODE=web \
    FLET_SERVER_IP=0.0.0.0

# Cloud Run injects $PORT; default to 8080 for local `docker run`.
EXPOSE 8080
CMD ["sh", "-c", "FLET_SERVER_PORT=${PORT:-8080} exec python main.py"]
