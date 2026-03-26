from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Tenant, KnowledgeBase # Added KnowledgeBase here
from app.schemas.schemas import OnboardRequest, OnboardResponse
from workers.tasks import crawl_and_embed_task
from app.routes.auth import get_current_user_email 

router = APIRouter()

@router.post("/", response_model=OnboardResponse)
def onboard_company(
    request: OnboardRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    verified_email: str = Depends(get_current_user_email)
):
    
    # 1. Check if a workspace already exists for this email
    tenant = db.query(Tenant).filter(Tenant.owner_email == verified_email).first()
    
    if not tenant:
        # Create a new workspace if they are brand new
        tenant = Tenant(
            name=request.name, 
            website_url=request.url,
            owner_email=verified_email, 
            tier="demo"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        
    # 2. DEDUPLICATION CHECK: Do we already have this URL saved for this tenant?
    existing_data = db.query(KnowledgeBase).filter(
        KnowledgeBase.tenant_id == tenant.id,
        KnowledgeBase.source_url == request.url
    ).first()
    
    if existing_data:
        # Stop immediately! Return success without triggering Firecrawl
        return OnboardResponse(
            status="Website already learned! Skipping duplicate scrape.", 
            tenant_id=tenant.id,
            tier=tenant.tier
        )
    
    # 3. If it's a new URL, kick off the background worker
    background_tasks.add_task(crawl_and_embed_task, request.url, tenant.id, db)
    
    return OnboardResponse(
        status="Researching site in background...", 
        tenant_id=tenant.id,
        tier=tenant.tier
    )