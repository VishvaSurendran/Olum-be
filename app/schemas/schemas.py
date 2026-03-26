from pydantic import BaseModel, EmailStr
from typing import List, Optional

# --- Chat Schemas ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    tenant_id: str
    question: str
    history: Optional[List[ChatMessage]] = []  # Defaults to empty list

class ChatResponse(BaseModel):
    answer: str

# --- Onboarding Schemas ---
class OnboardRequest(BaseModel):
    name: str
    url: str
    # Removed email! We will securely extract this from the JWT token instead.

class OnboardResponse(BaseModel):
    status: str
    tenant_id: str
    tier: str

# --- Authentication Schemas ---
class EmailRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    code: str

class GoogleAuthRequest(BaseModel):
    credential: str

class AnswerSubmission(BaseModel):
    question_id: int
    answer_text: str