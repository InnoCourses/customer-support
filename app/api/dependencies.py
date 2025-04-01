import os
from functools import lru_cache
from dotenv import load_dotenv
from database.supabase_db import SupabaseDB
from services.openai_service import OpenAIService
from services.issue_service import IssueService
from services.admin_service import AdminService
from services.faq_service import FAQService

# Load environment variables
load_dotenv()


@lru_cache()
def get_supabase_db():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    return SupabaseDB(supabase_url, supabase_key)


@lru_cache()
def get_openai_service():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    return OpenAIService(openai_api_key)


@lru_cache()
def get_issue_service():
    supabase_db = get_supabase_db()
    openai_service = get_openai_service()
    return IssueService(supabase_db, openai_service)


@lru_cache()
def get_admin_service():
    supabase_db = get_supabase_db()
    return AdminService(supabase_db)


@lru_cache()
def get_faq_service():
    supabase_db = get_supabase_db()
    openai_service = get_openai_service()
    return FAQService(supabase_db, openai_service)
