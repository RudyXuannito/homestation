from fastapi import FastAPI, Response, Request, Form
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sqlite3
import cv2
from fastapi import FastAPI, Form, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from db_setup import SessionLocal, engine, Base
from models import User
from itsdangerous import URLSafeTimedSerializer
from passlib.hash import bcrypt
import requests

app = FastAPI()

templates = Jinja2Templates(directory="templates", auto_reload=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Создание базы данных
Base.metadata.create_all(bind=engine)

# Секретный ключ для токенов
SECRET_KEY = "supersecretkey"
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Зависимость для базы данных
#def get_db():
#    db = SessionLocal()
#    try:
#        yield db
#    finally:
#        db.close()


# Подключаемся к базе данных SQLite
def get_db():
    conn = sqlite3.connect("/data/smart_home.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/registration", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})
# Обработка авторизации
@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "None username"},
        )

    if not user or not bcrypt.verify(password, user["hashed_password"]):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Invalid username or password"},
        )

    token = serializer.dumps(username)
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(key="session", value=token)
    return response


@app.post("/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
):
    conn = get_db()
    cursor = conn.cursor()
    hashed_password = bcrypt.hash(password)

    try:
        cursor.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            (username, hashed_password),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return {"message": "Username already exists"}
    finally:
        conn.close()

    return {"message": "User created successfully"}


# Панель управления
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    session = request.cookies.get("session")
    if not session:
        raise HTTPException(status_code=403, detail="No session found")

    try:
    
        conn = get_db()
        cursor = conn.cursor()
        conn.row_factory = sqlite3.Row  # <--- ВАЖНО!
        #cursor.execute("SELECT * FROM sensors_data")
        #sensors_name = cursor.fetchall()
        
        cameras = [
            {"id": 1, "name": "Camera 1", "url": "http://192.168.31.91/mjpeg/1"},
            {"id": 2, "name": "Camera 2", "url": "http://192.168.31.92/mjpeg/1"},
        ]
        cursor.execute("SELECT sensor_name, value FROM sensor_data")
        sensors = cursor.fetchall()
        #conn.close()
    
        sensor_readings = []
        for name, url in sensors:
            try:
                r = requests.get(url, timeout=3)
                data = r.json()
                sensor_readings.append({
                    "name": name,
                    "temperature": data.get("temperature"),
                    "humidity": data.get("humidity")
                })
            except Exception as e:
                sensor_readings.append({
                    "name": name,
                    "temperature": "error",
                    "humidity": "error"
                })


        conn.close()
        
        username = serializer.loads(session)
        return templates.TemplateResponse(
            "dashboard.html", {"request": request, "username": username, "cameras": cameras, "sensors": sensor_readings}
        )
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid session")

@app.get("/api/sensors")
async def get_sensor_data():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT sensor_name, value, value1 FROM sensor_data")
    sensors = cursor.fetchall()
    conn.close()

    all_sensors = []

    for name, url, type_ in sensors:
        if type_ == 'tandh':
            try:
                r = requests.get(url, timeout=10)
                data = r.json()
                all_sensors.append({
                    "name": name,
                    "type": "tandh",
                    "temperature": data.get("temperature"),
                    "humidity": data.get("humidity")
                })
            except Exception:
                all_sensors.append({
                    "name": name,
                    "type": "tandh",
                    "temperature": None,
                    "humidity": None
                })
        elif type_ == 'water':
            try:
                r = requests.get(url, timeout=10)
                data = r.json()
                all_sensors.append({
                    "name": name,
                    "type": "w",
                    "water": data.get("water")
                })
            except Exception:
                all_sensors.append({
                    "name": name,
                    "type": "w",
                    "water": None
                })
    return  all_sensors#, sensor_readingswater

@app.delete("/delete_sensor/{sensor_name}")
async def delete_sensor(sensor_name: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sensor_data WHERE sensor_name = ?", (sensor_name,))
    conn.commit()
    conn.close()
    return {"message": "Sensor deleted"}

# Добавление сенсора
@app.post("/addsensor")
async def addsensor(request: Request):
    data = await request.json()
    name = data.get("name")
    url = data.get("url")
    type_ = data.get("type_")

    if not all([name, url, type_]):
        return JSONResponse(status_code=400, content={"message": "Неверные данные"})

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO sensor_data (sensor_name, value, value1) VALUES (?, ?, ?)",
            (name, url, type_)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return JSONResponse(status_code=400, content={"message": "Сенсор уже существует"})
    finally:
        conn.close()

    return {"message": "Сенсор добавлен успешно"}
    

# Выход из системы
@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("session")
    return response

#
@app.get("/sensor")
def log_sensor_data():
    conn = sqlite3.connect("/data/smart_home.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensor_data")
    rows = cursor.fetchall()
    conn.close()
    return {"data": rows}
# LED камеры
@app.post("/control_led")
async def control_led(request: Request):
    try:
        data = await request.json()
        state = data.get("state")
        ip = data.get("ip", "192.168.31.91")  # по умолчанию — первая камера

        if state is None or not ip:
            return JSONResponse(content={"message": "Ошибка: отсутствует параметр"}, status_code=400)

        response = requests.get(f"http://{ip}/control", params={"state": state})

        if response.status_code == 200:
            return JSONResponse(content={"message": "LED state updated"}, status_code=200)
        else:
            return JSONResponse(content={"message": "Ошибка при отправке команды на ESP"}, status_code=500)

    except Exception as e:
        return JSONResponse(content={"message": f"Ошибка: {str(e)}"}, status_code=500)
#

@app.delete("/delete_camera/{camera_name}")
def delete_camera(camera_name: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cameras WHERE name = ?", (camera_name,))
    conn.commit()
    conn.close()
    return {"message": "Camera deleted"}

@app.post("/addcamera")
async def add_camera(request: Request):
    data = await request.json()
    name = data.get("name")
    url = data.get("url")

    if not all([name, url]):
        return JSONResponse(status_code=400, content={"message": "Недостаточно данных"})

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO cameras (name, camurl) VALUES (?, ?)", (name, url))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return JSONResponse(status_code=400, content={"message": "Камера уже существует"})
    finally:
        conn.close()

    return {"message": "Камера добавлена"}

@app.get("/api/cameras")
def get_cameras():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, camurl FROM cameras")
    cameras = cursor.fetchall()
    conn.close()
    return [{"name": row[0], "url": row[1]} for row in cameras]

@app.get("/video_stream")
def video_stream(url: str):
    cap = cv2.VideoCapture(url)

    def generate():
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/video")
def video_feed():
    esp32_url = "http://192.168.31.92/mjpeg/1"
    cap = cv2.VideoCapture(esp32_url)

    def generate():
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")
