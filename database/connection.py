
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)
Base = declarative_base()

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.engine = None
            cls._instance.SessionFactory = None
        return cls._instance

    def connect(self, connection_string):
        """
        Connect to a database given a connection string.
        Example strings:
        - sqlite:///data/timetracker.db
        - postgresql://user:pass@localhost:5432/dbname
        - mysql+pymysql://user:pass@localhost:3306/dbname
        """
        try:
            logger.info(f"Connecting to database: {connection_string}")
            self.engine = create_engine(connection_string, echo=False)
            
            # Test the connection
            with self.engine.connect() as conn:
                logger.info("Database connection established successfully.")
            
            self.SessionFactory = sessionmaker(bind=self.engine)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.engine = None
            self.SessionFactory = None
            return False

    def get_session(self):
        if not self.SessionFactory:
            raise Exception("Database not connected. Call connect() first.")
        return scoped_session(self.SessionFactory)

    def init_database(self):
        """Creates tables based on models if they don't exist."""
        if not self.engine:
             raise Exception("Database not connected.")
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables initialized.")
            return True
        except Exception as e:
            logger.error(f"Error initializing tables: {e}")
            return False

db_manager = DatabaseManager()
