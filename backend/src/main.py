import os

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # Load env before importing modules that read DB settings.

from src.routes.analyze import router as analyze_router
from src.routes.tickets import router as tickets_router

app = FastAPI()

raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
if not allow_origins:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/analyze", tags=["analyze"])
app.include_router(tickets_router, prefix="/tickets", tags=["tickets"])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-health")
def db_health():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "supportflow")
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result and result[0] == 1:
            return {"db": "ok"}
        else:
            raise HTTPException(status_code=500, detail="Unexpected DB response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
