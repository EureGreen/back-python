from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, permissions, resources
from app.database import engine, Base

# Создание таблиц (для разработки)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth System API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(permissions.router)
app.include_router(resources.router)

@app.get("/")
def root():
    return {
        "message": "Auth System API",
        "version": "1.0.0",
        "endpoints": [
            "/auth/register",
            "/auth/login",
            "/auth/logout",
            "/auth/me",
            "/users/me",
            "/api/products",
            "/api/orders",
            "/admin/permissions",
            "/admin/roles"
        ]
    }