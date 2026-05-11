FROM python:3.11-slim

WORKDIR /app

RUN printf "deb http://deb.debian.org/debian bookworm main\n\
deb http://deb.debian.org/debian-security bookworm-security main\n\
deb http://deb.debian.org/debian bookworm-updates main\n" \
> /etc/apt/sources.list

RUN apt-get update

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
