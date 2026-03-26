from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import random
import string
from datetime import datetime, timedelta
import jwt
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.db.database import get_db
from app.models.models import OTPVerification, Tenant
from app.services.email_srv import send_otp_email
from app.schemas.schemas import EmailRequest, OTPVerifyRequest, GoogleAuthRequest

router = APIRouter()
security = HTTPBearer() # Tells FastAPI to look for an Authorization header

JWT_SECRET = os.getenv("JWT_SECRET", "fallback_secret")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# --- Helper: Generate JWT ---
def create_session_token(email: str):
    expiration = datetime.utcnow() + timedelta(days=7)
    payload = {"sub": email, "exp": expiration}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# --- THE BOUNCER: Decode JWT for secure routes ---
def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub") # Returns the securely verified email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid auth token.")

# --- Routes ---
@router.post("/request-otp")
def request_otp(request: EmailRequest, db: Session = Depends(get_db)):
    code = ''.join(random.choices(string.digits, k=6))
    expiration = datetime.utcnow() + timedelta(minutes=10)
    
    existing_otp = db.query(OTPVerification).filter(OTPVerification.email == request.email).first()
    if existing_otp:
        existing_otp.otp_code = code
        existing_otp.expires_at = expiration
    else:
        new_otp = OTPVerification(email=request.email, otp_code=code, expires_at=expiration)
        db.add(new_otp)
    db.commit()
    
    send_otp_email(request.email, code)
    return {"message": "OTP sent to your email."}

@router.post("/verify-otp")
def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    record = db.query(OTPVerification).filter(OTPVerification.email == request.email).first()
    
    if not record or record.otp_code != request.code:
        raise HTTPException(status_code=400, detail="Invalid OTP code.")
    if datetime.utcnow() > record.expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
        
    db.delete(record)
    db.commit()
    
    token = create_session_token(request.email)
    tenant = db.query(Tenant).filter(Tenant.owner_email == request.email).first()
    
    return {
        "access_token": token, 
        "tenant_id": tenant.id if tenant else None,
        "message": "Login successful"
    }

@router.post("/google")
def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(request.credential, google_requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo['email']
        
        token = create_session_token(email)
        tenant = db.query(Tenant).filter(Tenant.owner_email == email).first()
        
        return {
            "access_token": token, 
            "tenant_id": tenant.id if tenant else None,
            "message": "Google Login successful"
        }
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")