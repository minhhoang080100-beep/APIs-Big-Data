"""
Database connection module for SQL Server
"""
import pyodbc
import logging
import os
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """SQL Server connection manager for SmartTOS database"""
    
    def __init__(self):
        """Initialize database connection parameters"""
        self.server = os.getenv("DB_SERVER", "Tosdb.nghetinhport.vn\\mssqlserver,37689")
        self.database = os.getenv("DB_DATABASE", "SmartTOS")
        self.username = os.getenv("DB_USERNAME", "nghetinhport_readonly")
        self.password = os.getenv("DB_PASSWORD", "")
        self.driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
        
        if not self.password:
            logger.warning("DB_PASSWORD not set in environment variables")
        
        logger.info(f"Database initialized: {self.database} on {self.server}")
    
    def get_connection_string(self) -> str:
        """Build ODBC connection string"""
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes"
        )
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connection
        
        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                # do something
        """
        conn = None
        try:
            conn = pyodbc.connect(self.get_connection_string(), timeout=30)
            logger.debug("Database connection established")
            yield conn
        except pyodbc.Error as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("Database connection closed")
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return results as list of dictionaries
        
        Args:
            query: SQL SELECT query
            params: Query parameters (optional)
            
        Returns:
            List of dictionaries with column names as keys
            
        Example:
            results = db.execute_query(
                "SELECT * FROM dbo.Partner WHERE partnerCode = ?",
                (customer_code,)
            )
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Get column names
                columns = [column[0] for column in cursor.description]
                
                # Fetch all rows and convert to list of dicts
                results = []
                for row in cursor.fetchall():
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Convert datetime to ISO string
                        if hasattr(value, 'isoformat'):
                            row_dict[columns[i]] = value.isoformat()
                        else:
                            row_dict[columns[i]] = value
                    results.append(row_dict)
                
                logger.info(f"Query executed successfully. Returned {len(results)} rows")
                return results
                
        except pyodbc.Error as e:
            logger.error(f"Query execution error: {str(e)}")
            logger.error(f"Query: {query}")
            raise
    
    def execute_scalar(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> Any:
        """
        Execute query and return single value
        
        Args:
            query: SQL query
            params: Query parameters (optional)
            
        Returns:
            Single scalar value
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except pyodbc.Error as e:
            logger.error(f"Scalar query error: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    logger.info("✓ Database connection test successful")
                    return True
                else:
                    logger.error("✗ Database connection test failed")
                    return False
                    
        except Exception as e:
            logger.error(f"✗ Database connection test failed: {str(e)}")
            return False


# Global database instance
db = DatabaseConnection()


if __name__ == "__main__":
    """Test database connection"""
    logging.basicConfig(level=logging.INFO)
    
    print("Testing SQL Server connection...")
    print(f"Server: {db.server}")
    print(f"Database: {db.database}")
    print()
    
    # Test connection
    if db.test_connection():
        print("✓ Connection successful!")
        
        # Test query
        print("\nTesting sample query...")
        try:
            results = db.execute_query("SELECT TOP 5 partnerCode, partnerShortName FROM dbo.Partner")
            print(f"✓ Query successful! Found {len(results)} records:")
            for row in results:
                print(f"  - {row}")
        except Exception as e:
            print(f"✗ Query failed: {str(e)}")
    else:
        print("✗ Connection failed!")
