FROM python:3.11-alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . .

RUN mkdir /etc/init.d/

RUN apk add --no-cache curl unzip

RUN curl -L https://raw.githubusercontent.com/XTLS/alpinelinux-install-xray/main/install-release.sh | ash

RUN apk add --no-cache alpine-sdk libffi-dev && pip install --no-cache-dir -r /app/requirements.txt && apk del -r alpine-sdk libffi-dev curl unzip

CMD ["python3", "marznode.py"]
