from app.core.celery_app import celery_app
from app.services.rag.document_loader import load_document
from app.services.embedding.factory import get_embedding_model
from app.services.vector_store.factory import get_vector_store
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.crud.crud_document import document_crud
from app.core.database import engine
import asyncio
def process_document():
    return None