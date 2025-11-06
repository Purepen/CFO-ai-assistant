#%%
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")  # Optional for now
    
    # Model Settings
    ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
    TEMPERATURE = 0
    MAX_TOKENS = 4096
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
    DOCUMENTS_DIR = os.path.join(DATA_DIR, "documents")
    DATABASE_DIR = os.path.join(BASE_DIR, "database")
    VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")
    
    # Database
    DATABASE_PATH = os.path.join(DATABASE_DIR, "financial.db")
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    
    # Vector Store
    COLLECTION_NAME = "financial_policies"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # Search
    MAX_SEARCH_RESULTS = 5
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        dirs = [
            cls.DATA_DIR,
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.DOCUMENTS_DIR,
            cls.DATABASE_DIR,
            cls.VECTORSTORE_DIR
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)

# Create directories on import
Config.create_directories()
# %%
