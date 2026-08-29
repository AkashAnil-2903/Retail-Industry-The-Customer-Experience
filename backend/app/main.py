from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .database import engine, SessionLocal, Base
from .seed.seed_data import seed_database
from .routers import auth, employee, courses, simulation, manager, admin, challenges
from .routers import manager_hierarchical

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Workforce Coach", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(employee.router)
app.include_router(courses.router)
app.include_router(simulation.router)
app.include_router(manager.router)
app.include_router(admin.router)
app.include_router(challenges.router)
app.include_router(manager_hierarchical.router)


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "AI Workforce Coach"}


# Serve static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    # Serve index.html for SPA routing (skip API routes)
    if full_path.startswith("api/"):
        return {"error": "not found"}
    file_path = os.path.join(static_dir, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(static_dir, "index.html"))
