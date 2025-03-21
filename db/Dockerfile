FROM alpine:latest

# Установка sqlite3
RUN apk add --no-cache sqlite

# Установка рабочей директории
WORKDIR /data

# Запуск sqlite3 как основной процесс
ENTRYPOINT ["sqlite3"]
