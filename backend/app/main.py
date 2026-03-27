from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.routes import user_routes, employee_routes
from app.db.indexes import create_indexes

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]
    app.state.users_collection = db["users"]
    app.state.employees_collection = db["employees"]
    await create_indexes(app.state.users_collection, app.state.employees_collection)
    yield
    client.close()

app = FastAPI(title="Employee Management System API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://204.236.210.174",
        "https://d2ipaljcx1vm6z.cloudfront.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_routes.router, prefix="/auth", tags=["auth"])
app.include_router(employee_routes.router, prefix="/employees", tags=["employees"])

@app.get("/health")
async def health():
    return {"status": "ok"}
