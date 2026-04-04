import sqlite3
import logging
from backend.config import settings

logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations manually for SQLite."""
    db_path = settings.database_url.replace("sqlite:///", "")
    if not db_path.startswith("/"):
        # Handle relative paths if necessary (though usually it's absolute in Docker)
        import os
        db_path = os.path.join(os.getcwd(), db_path)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if download_dir column exists in playlists table
        cursor.execute("PRAGMA table_info(playlists)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "download_dir" not in columns:
            logger.info("Adding missing 'download_dir' column to 'playlists' table...")
            cursor.execute("ALTER TABLE playlists ADD COLUMN download_dir VARCHAR(500)")
            conn.commit()
            logger.info("Column 'download_dir' added successfully.")
        else:
            logger.debug("Column 'download_dir' already exists.")
            
        conn.close()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # We don't raise error here to allow create_all to try its best, 
        # but the app might fail later if this isn't fixed.
