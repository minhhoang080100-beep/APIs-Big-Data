"""
Configuration module for API client
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """API Configuration"""
    
    # API Base URL
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://api.example.com')
    
    # Authentication
    API_USERNAME = os.getenv('API_USERNAME', '')
    API_PASSWORD = os.getenv('API_PASSWORD', '')
    
    # Token settings
    ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', '')
    TOKEN_EXPIRY = os.getenv('TOKEN_EXPIRY', '')
    
    # API Endpoints
    LOGIN_ENDPOINT = '/api/login'
    
    # Request timeout (seconds)
    REQUEST_TIMEOUT = 30
    
    # Token expiration time (hours)
    TOKEN_EXPIRATION_HOURS = 8
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.API_USERNAME or not cls.API_PASSWORD:
            raise ValueError("API_USERNAME and API_PASSWORD must be set in .env file")
        return True
