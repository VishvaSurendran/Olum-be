from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.models.models import UnansweredQuestion, KnowledgeBase
from app.services.embedding_srv import process_and_embed_markdown
from app.schemas.schemas import AnswerSubmission

router = APIRouter()

@router.get("/pending/{tenant_id}")
def get_pending_questions(tenant_id: str, db: Session = Depends(get_db)):
    """Fetches all unanswered questions for the admin dashboard."""
    questions = db.query(UnansweredQuestion).filter(
        UnansweredQuestion.tenant_id == tenant_id,
        UnansweredQuestion.is_answered == 0
    ).all()
    
    return {"pending_questions": questions}

@router.post("/teach")
def teach_bot(submission: AnswerSubmission, db: Session = Depends(get_db)):
    """Takes the admin's answer, embeds it, and adds it to the AI's brain."""
    
    q_record = db.query(UnansweredQuestion).filter(UnansweredQuestion.id == submission.question_id).first()
    if not q_record:
        raise HTTPException(status_code=404, detail="Question not found")
        
    training_text = f"Question: {q_record.question}\nAnswer: {submission.answer_text}"
    
    chunked_data = process_and_embed_markdown(training_text)
    
    source_identifier = f"manual_qa:{q_record.id}"
    
    for chunk, vector in chunked_data:
        new_kb_entry = KnowledgeBase(
            tenant_id=q_record.tenant_id,
            content=chunk,
            source_url=source_identifier,
            embedding=vector
        )
        db.add(new_kb_entry)
        
    q_record.is_answered = 1
    db.commit()
    
    return {"status": "Bot trained successfully! It now knows the answer to this question."}