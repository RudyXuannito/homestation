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

templates = Jinja2Templates(directory="templates")
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
        
        cursor.execute("SELECT * FROM sensor_data")
        sensors = cursor.fetchall()
        
        # Пример данных для камер (можете расширить для реальных данных)
        cameras = [
            {"id": 1, "name": "Camera 1", "url": "http://192.168.31.91/mjpeg/1"},
            {"id": 2, "name": "Camera 2", "url": "http://192.168.31.92/mjpeg/1"},
        ]

        conn.close()
        
        username = serializer.loads(session)
        return templates.TemplateResponse(
            "dashboard.html", {"request": request, "username": username, "cameras": cameras, "sensors": sensors}
        )
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid session")

# Добавление сенсора
@app.post("/add_sensor", response_class=HTMLResponse)
async def add_sensor(
    request: Request,
    sensor_name: str = Form(...),
    sensor_address: str = Form(...),
):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO sensor_data (sensor_name, value) VALUES (?, ?)",
            (sensor_name, sensor_address),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Sensor already exists"},
        )
    finally:
        conn.close()

    return RedirectResponse("/dashboard", status_code=303)
    

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
        data = await request.json()  # Ждем JSON
        state = data.get("state")

        if state is None:
            return JSONResponse(content={"message": "Ошибка: отсутствует state"}, status_code=400)

        response = requests.get("http://192.168.31.91/control", params={"state": state})

        if response.status_code == 200:
            return JSONResponse(content={"message": "LED state updated"}, status_code=200)
        else:
            return JSONResponse(content={"message": "Ошибка при отправке команды на ESP32"}, status_code=500)

    except Exception as e:
        return JSONResponse(content={"message": f"Ошибка: {str(e)}"}, status_code=500)
#
        
@app.get("/video")
def video_feed():
    esp32_url = "http://192.168.31.91/mjpeg/1"
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
