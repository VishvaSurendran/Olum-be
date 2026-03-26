from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine
from app.models import models
from app.routes import onboard, chat, documents, training, auth

# Initialize tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chat-With-Website Engine", version="1.0.0")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(onboard.router, prefix="/api/onboard", tags=["Onboarding"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(training.router, prefix="/api/training", tags=["Bot Training"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

@app.get("/")
def health_check():
    return {"status": "healthy", "message": "Backend engine is running."}