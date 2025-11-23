FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Accept build-time variables
ARG PROJECT_NAME
ARG DEV_PORT

# Use default values if not passed
ENV PROJECT_NAME=${PROJECT_NAME}
ENV DEV_PORT=${DEV_PORT}

WORKDIR /code

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["daphne", "-b", "0.0.0.0", "-p", "${DEV_PORT}", "${PROJECT_NAME}.asgi:application"]
