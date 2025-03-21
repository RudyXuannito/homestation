# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем зависимости
WORKDIR /api
COPY . /api
RUN pip install --no-cache-dir fastapi uvicorn
#
RUN pip install --no-cache-dir python-multipart
RUN pip install --no-cache-dir passlib[bcrypt]
RUN pip install --no-cache-dir opencv-python
RUN pip install --no-cache-dir requests
COPY ./requirements.txt /api
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH="/" 
#
# Указываем команду для запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
