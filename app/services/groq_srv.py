import os
from groq import Groq
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_srv import model
from app.core.config import GROQ_API_KEY
from app.models.models import UnansweredQuestion
from app.services.email_srv import send_unanswered_question_email

client = Groq(api_key=GROQ_API_KEY)

def answer_visitor_question(
    tenant_id: str, 
    question: str, 
    db: Session, 
    history: list = None, 
    background_tasks: BackgroundTasks = None, 
    admin_email: str = None
):
    history = history or []
    question_vector = model.encode(question).tolist()
    
    query = text("""
        SELECT content 
        FROM knowledge_base 
        WHERE tenant_id = :tenant_id 
        ORDER BY embedding <=> :question_vector 
        LIMIT 3
    """)
    
    results = db.execute(query, {
        "tenant_id": tenant_id, 
        "question_vector": str(question_vector)
    }).fetchall()
    
    context = "\n\n".join([row[0] for row in results]) if results else "No company data available yet."
    
    system_prompt = f"""
    You are a helpful, polite customer support bot for a company. 
    You have access to the conversation history. Use it to understand the context of the user's latest reply.
    
    CRITICAL RULES:
    1. SMALL TALK: If the user says a greeting or makes a brief acknowledgment (okay, sure, yes) THAT DOES NOT relate to an ongoing conversation about services, respond politely. 
    2. COMPANY QUESTIONS: If the user asks a specific question, or agrees to hear more about a topic you just brought up, answer ONLY using the "Context" below.
    3. THE SECRET FALLBACK: If the user asks a factual company question and the exact answer is NOT clearly stated in the Context below, reply with exactly: SYS_NOT_FOUND
    
    Context from company website:
    {context}
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in history[-6:]:
        groq_role = "assistant" if msg.role == "bot" else "user"
        messages.append({"role": groq_role, "content": msg.content})
        
    messages.append({"role": "user", "content": question})
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.1, 
        max_tokens=500
    )
    
    answer = completion.choices[0].message.content.strip()
    
    if "SYS_NOT_FOUND" in answer:
        # 1. Save to Database
        new_pending_q = UnansweredQuestion(tenant_id=tenant_id, question=question)
        db.add(new_pending_q)
        db.commit()
        
        # 2. Trigger the Email Alert in the background
        if background_tasks and admin_email:
            background_tasks.add_task(send_unanswered_question_email, admin_email, question)
            
        return "I apologize, but I don't have that exact information right now. I have noted your question for our team to review and answer shortly!"
    
    return answer