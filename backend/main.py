# backend/main.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ^ adds project root to path so "research.*" and "backend.*" both import cleanly

from dotenv import load_dotenv
# Explicitly load the .env file located in the same directory as main.py
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes import query, upload, attack, collections

app = FastAPI(title="Secure RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(upload.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(attack.router, prefix="/api")
app.include_router(collections.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "Secure RAG API running"}
