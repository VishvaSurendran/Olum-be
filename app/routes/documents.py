from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import KnowledgeBase
from app.services.document_srv import extract_text_from_file
from workers.tasks import process_and_embed_document_task

router = APIRouter()

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    tenant_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. DEDUPLICATION CHECK: Does this exact file name already exist for this tenant?
    source_identifier = f"doc:{file.filename}"
    existing_doc = db.query(KnowledgeBase).filter(
        KnowledgeBase.tenant_id == tenant_id,
        KnowledgeBase.source_url == source_identifier
    ).first()
    
    if existing_doc:
        # Tell the frontend it's already there to save processing power
        return {
            "status": "Document already exists in the knowledge base. If you want to update it, please delete the old one first.", 
            "filename": file.filename
        }

    # 2. Proceed with heavy lifting if it's new
    file_bytes = await file.read()
    
    try:
        extracted_text = extract_text_from_file(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    background_tasks.add_task(process_and_embed_document_task, extracted_text, file.filename, tenant_id, db)
    
    return {"status": "Document parsing and embedding started in background.", "filename": file.filename}

@router.delete("/{tenant_id}/{filename}")
def delete_document(tenant_id: str, filename: str, db: Session = Depends(get_db)):
    source_identifier = f"doc:{filename}"
    
    deleted_count = db.query(KnowledgeBase).filter(
        KnowledgeBase.tenant_id == tenant_id,
        KnowledgeBase.source_url == source_identifier
    ).delete()
    
    db.commit()
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found or already deleted.")
        
    return {"status": "Deleted successfully", "chunks_removed": deleted_count}

@router.get("/list/{tenant_id}")
def list_documents(tenant_id: str, db: Session = Depends(get_db)):
    # Find all unique document source_urls for this tenant
    docs = db.query(KnowledgeBase.source_url).filter(
        KnowledgeBase.tenant_id == tenant_id,
        KnowledgeBase.source_url.like("doc:%")
    ).distinct().all()
    
    # Strip out the "doc:" prefix to just send the clean filenames to the frontend
    filenames = [doc[0].replace("doc:", "") for doc in docs]
    
    return {"documents": filenames}