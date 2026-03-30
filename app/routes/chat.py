from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Tenant
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.groq_srv import answer_visitor_question

router = APIRouter()

@router.post("/", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    
    # 1. Fetch the tenant to check billing status and grab their email
    tenant = db.query(Tenant).filter(Tenant.id == request.tenant_id).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Company bot not found.")

    # 2. The Paywall Logic
    # if tenant.tier == "demo" and tenant.message_count >= 5:
    if tenant.tier == "demo" and tenant.message_count >= 10:
        paywall_msg = "LIMIT_REACHED: Your bot is performing beautifully! 🚀 To unlock unlimited chats, deep-site crawling, and to embed this bot on your own website, please upgrade to a Pro plan."
        return ChatResponse(answer=paywall_msg)

    # 3. Generate answer (Now we pass background_tasks and the owner's email!)
    answer = answer_visitor_question(
        tenant_id=request.tenant_id, 
        question=request.question, 
        db=db, 
        history=request.history,
        background_tasks=background_tasks,
        admin_email=tenant.owner_email
    )
    
    # 4. Increment message count
    tenant.message_count += 1
    db.commit()
    
    return ChatResponse(answer=answer)