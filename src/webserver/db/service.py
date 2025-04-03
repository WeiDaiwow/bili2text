import sqlite3
import os
import json
import time
import threading
from datetime import datetime

class DatabaseService:
    """Service for interacting with SQLite database for Bili2Text."""
    
    def __init__(self, db_path="data/bili2text.db"):
        """
        Initialize the database service.
        
        Args:
            db_path: Path to the SQLite database file
        """
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        # Use thread-local storage for database connections
        self.local = threading.local()
        
        # Initialize database
        self._connect()
        self._create_tables()
        self._disconnect()
    
    def _connect(self):
        """Establish a connection to the database."""
        if not hasattr(self.local, 'connection') or self.local.connection is None:
            self.local.connection = sqlite3.connect(self.db_path)
            self.local.connection.row_factory = sqlite3.Row  # Return rows as dict-like objects
            self.local.cursor = self.local.connection.cursor()
    
    def _disconnect(self):
        """Close the database connection."""
        if hasattr(self.local, 'connection') and self.local.connection:
            self.local.connection.close()
            self.local.connection = None
            self.local.cursor = None
    
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        # Videos table
        self.local.cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bv_number TEXT NOT NULL UNIQUE,
            title TEXT,
            author TEXT,
            download_date TEXT NOT NULL,
            video_path TEXT NOT NULL,
            audio_path TEXT,
            thumbnail_path TEXT,
            duration REAL,
            resolution TEXT,
            status TEXT DEFAULT 'downloaded',
            metadata TEXT
        )
        ''')
        
        # Transcriptions table
        self.local.cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            engine TEXT NOT NULL,
            transcription_date TEXT NOT NULL,
            text TEXT NOT NULL,
            confidence REAL,
            status TEXT DEFAULT 'completed',
            FOREIGN KEY (video_id) REFERENCES videos (id)
        )
        ''')
        
        # Tags table
        self.local.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#3498db',
            created_at TEXT NOT NULL
        )
        ''')
        
        # Video-Tags relation table (many-to-many)
        self.local.cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_tags (
            video_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            added_at TEXT NOT NULL,
            PRIMARY KEY (video_id, tag_id),
            FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        )
        ''')
        
        self.local.connection.commit()
    
    def add_video(self, bv_number, video_path, title=None, author=None, 
                  audio_path=None, thumbnail_path=None, duration=None, 
                  resolution=None, metadata=None, status="downloaded"):
        """
        Add a new video to the database.
        
        Args:
            bv_number: BV number of the video
            video_path: Path to the video file
            title: Title of the video
            author: Author of the video
            audio_path: Path to the extracted audio file
            thumbnail_path: Path to the video thumbnail
            duration: Duration of the video in seconds
            resolution: Resolution of the video
            metadata: Additional metadata as a dictionary
            status: Status of the video processing
            
        Returns:
            ID of the inserted video record
        """
        try:
            self._connect()
            
            # Convert metadata to JSON string if provided
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Current timestamp
            download_date = datetime.now().isoformat()
            
            self.local.cursor.execute('''
            INSERT INTO videos (
                bv_number, title, author, download_date, video_path, 
                audio_path, thumbnail_path, duration, resolution, metadata, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bv_number, title, author, download_date, video_path,
                audio_path, thumbnail_path, duration, resolution, metadata_json, status
            ))
            
            self.local.connection.commit()
            return self.local.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Video with this BV number already exists
            self.local.cursor.execute("SELECT id FROM videos WHERE bv_number = ?", (bv_number,))
            result = self.local.cursor.fetchone()
            return result['id'] if result else None
        finally:
            self._disconnect()
    
    def update_video(self, video_id, **kwargs):
        """
        Update an existing video record.
        
        Args:
            video_id: ID of the video to update
            **kwargs: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._connect()
            
            # Process metadata if provided
            if 'metadata' in kwargs and isinstance(kwargs['metadata'], dict):
                kwargs['metadata'] = json.dumps(kwargs['metadata'])
            
            # Build UPDATE statement
            fields = []
            values = []
            
            for key, value in kwargs.items():
                fields.append(f"{key} = ?")
                values.append(value)
            
            if not fields:
                return False
                
            values.append(video_id)
            
            query = f"UPDATE videos SET {', '.join(fields)} WHERE id = ?"
            self.local.cursor.execute(query, values)
            self.local.connection.commit()
            
            return self.local.cursor.rowcount > 0
        finally:
            self._disconnect()
    
    def get_video(self, video_id=None, bv_number=None):
        """
        Get a video record by ID or BV number.
        
        Args:
            video_id: ID of the video
            bv_number: BV number of the video
            
        Returns:
            Video record as a dictionary
        """
        try:
            self._connect()
            
            if video_id:
                self.local.cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
            elif bv_number:
                self.local.cursor.execute("SELECT * FROM videos WHERE bv_number = ?", (bv_number,))
            else:
                return None
                
            result = self.local.cursor.fetchone()
            
            if result:
                # Convert row to dictionary
                video = dict(result)
                
                # Parse metadata JSON
                if video.get('metadata'):
                    try:
                        video['metadata'] = json.loads(video['metadata'])
                    except json.JSONDecodeError:
                        pass
                        
                return video
            
            return None
        finally:
            self._disconnect()
    
    def get_all_videos(self, limit=100, offset=0, order_by="download_date DESC", tag_id=None):
        """
        Get all video records with pagination and optional filtering.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Column to order by
            tag_id: Optional tag ID to filter by
            
        Returns:
            List of video records as dictionaries and total count
        """
        try:
            self._connect()
            
            # Get total count first, before fetching the actual data
            if tag_id:
                # Get total count for tagged videos
                self.local.cursor.execute(
                    "SELECT COUNT(*) FROM videos v JOIN video_tags vt ON v.id = vt.video_id WHERE vt.tag_id = ?", 
                    (tag_id,)
                )
            else:
                # Get total count for all videos
                self.local.cursor.execute("SELECT COUNT(*) FROM videos")
                
            # Get total count
            total_count_row = self.local.cursor.fetchone()
            total_count = total_count_row[0] if total_count_row else 0
            
            # Now get the actual data
            if tag_id:
                # Get videos with specific tag
                query = f"""
                SELECT v.* FROM videos v
                JOIN video_tags vt ON v.id = vt.video_id
                WHERE vt.tag_id = ?
                ORDER BY {order_by} 
                LIMIT ? OFFSET ?
                """
                self.local.cursor.execute(query, (tag_id, limit, offset))
            else:
                # Get all videos
                query = f"SELECT * FROM videos ORDER BY {order_by} LIMIT ? OFFSET ?"
                self.local.cursor.execute(query, (limit, offset))
                
            # Get results
            results = self.local.cursor.fetchall()
            
            videos = []
            for result in results:
                video = dict(result)
                
                # Parse metadata JSON
                if video.get('metadata'):
                    try:
                        video['metadata'] = json.loads(video['metadata'])
                    except json.JSONDecodeError:
                        pass
                
                # Get tags for this video
                self.local.cursor.execute("""
                SELECT t.* FROM tags t
                JOIN video_tags vt ON t.id = vt.tag_id
                WHERE vt.video_id = ?
                """, (video['id'],))
                video['tags'] = [dict(tag) for tag in self.local.cursor.fetchall()]
                
                videos.append(video)
                
            return videos, total_count
        finally:
            self._disconnect()
    
    def add_transcription(self, video_id, text, engine, confidence=None):
        """
        Add a new transcription record.
        
        Args:
            video_id: ID of the associated video
            text: Transcribed text
            engine: Name of the transcription engine
            confidence: Confidence score (0-1)
            
        Returns:
            ID of the inserted transcription record
        """
        try:
            self._connect()
            
            # Current timestamp
            transcription_date = datetime.now().isoformat()
            
            self.local.cursor.execute('''
            INSERT INTO transcriptions (
                video_id, engine, transcription_date, text, confidence
            ) VALUES (?, ?, ?, ?, ?)
            ''', (
                video_id, engine, transcription_date, text, confidence
            ))
            
            self.local.connection.commit()
            
            # Update video status
            self.local.cursor.execute(
                "UPDATE videos SET status = 'transcribed' WHERE id = ?", 
                (video_id,)
            )
            self.local.connection.commit()
            
            return self.local.cursor.lastrowid
        finally:
            self._disconnect()
    
    def get_transcription(self, transcription_id=None, video_id=None, latest=True):
        """
        Get a transcription record by ID or video ID.
        
        Args:
            transcription_id: ID of the transcription
            video_id: ID of the associated video
            latest: If True and using video_id, get only the latest transcription
            
        Returns:
            Transcription record as a dictionary
        """
        try:
            self._connect()
            
            if transcription_id:
                self.local.cursor.execute("SELECT * FROM transcriptions WHERE id = ?", (transcription_id,))
                result = self.local.cursor.fetchone()
                return dict(result) if result else None
            elif video_id:
                if latest:
                    self.local.cursor.execute(
                        "SELECT * FROM transcriptions WHERE video_id = ? ORDER BY transcription_date DESC LIMIT 1", 
                        (video_id,)
                    )
                    result = self.local.cursor.fetchone()
                    return dict(result) if result else None
                else:
                    self.local.cursor.execute(
                        "SELECT * FROM transcriptions WHERE video_id = ? ORDER BY transcription_date DESC", 
                        (video_id,)
                    )
                    results = self.local.cursor.fetchall()
                    return [dict(row) for row in results] if results else []
            
            return None
        finally:
            self._disconnect()
    
    def delete_video(self, video_id):
        """
        Delete a video and its transcriptions from the database.
        
        Args:
            video_id: ID of the video to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._connect()
            
            # Delete transcriptions will be cascaded due to foreign key constraint
            
            # Delete the video
            self.local.cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
            
            self.local.connection.commit()
            return self.local.cursor.rowcount > 0
        finally:
            self._disconnect()

    # Tag management methods
    def add_tag(self, name, color="#3498db"):
        """
        Add a new tag.
        
        Args:
            name: Name of the tag
            color: Color of the tag (hexadecimal)
            
        Returns:
            ID of the inserted tag record
        """
        try:
            self._connect()
            
            created_at = datetime.now().isoformat()
            
            self.local.cursor.execute(
                "INSERT INTO tags (name, color, created_at) VALUES (?, ?, ?)",
                (name, color, created_at)
            )
            
            self.local.connection.commit()
            return self.local.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Tag with this name already exists
            self.local.cursor.execute("SELECT id FROM tags WHERE name = ?", (name,))
            result = self.local.cursor.fetchone()
            return result['id'] if result else None
        finally:
            self._disconnect()
    
    def get_all_tags(self):
        """
        Get all tags.
        
        Returns:
            List of tag records as dictionaries
        """
        try:
            self._connect()
            
            self.local.cursor.execute("SELECT * FROM tags ORDER BY name")
            return [dict(row) for row in self.local.cursor.fetchall()]
        finally:
            self._disconnect()
    
    def add_tag_to_video(self, video_id, tag_id):
        """
        Add a tag to a video.
        
        Args:
            video_id: ID of the video
            tag_id: ID of the tag
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._connect()
            
            added_at = datetime.now().isoformat()
            
            self.local.cursor.execute(
                "INSERT OR IGNORE INTO video_tags (video_id, tag_id, added_at) VALUES (?, ?, ?)",
                (video_id, tag_id, added_at)
            )
            
            self.local.connection.commit()
            return self.local.cursor.rowcount > 0
        finally:
            self._disconnect()
    
    def remove_tag_from_video(self, video_id, tag_id):
        """
        Remove a tag from a video.
        
        Args:
            video_id: ID of the video
            tag_id: ID of the tag
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._connect()
            
            self.local.cursor.execute(
                "DELETE FROM video_tags WHERE video_id = ? AND tag_id = ?",
                (video_id, tag_id)
            )
            
            self.local.connection.commit()
            return self.local.cursor.rowcount > 0
        finally:
            self._disconnect()
    
    def get_video_tags(self, video_id):
        """
        Get all tags for a video.
        
        Args:
            video_id: ID of the video
            
        Returns:
            List of tag records as dictionaries
        """
        try:
            self._connect()
            
            self.local.cursor.execute("""
            SELECT t.* FROM tags t
            JOIN video_tags vt ON t.id = vt.tag_id
            WHERE vt.video_id = ?
            ORDER BY t.name
            """, (video_id,))
            
            return [dict(row) for row in self.local.cursor.fetchall()]
        finally:
            self._disconnect()
    
    def get_videos_with_tag(self, tag_id, limit=100, offset=0):
        """
        Get all videos with a specific tag.
        
        Args:
            tag_id: ID of the tag
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of video records as dictionaries
        """
        try:
            self._connect()
            
            self.local.cursor.execute("""
            SELECT v.* FROM videos v
            JOIN video_tags vt ON v.id = vt.video_id
            WHERE vt.tag_id = ?
            ORDER BY v.download_date DESC
            LIMIT ? OFFSET ?
            """, (tag_id, limit, offset))
            
            results = self.local.cursor.fetchall()
            videos = []
            
            for result in results:
                video = dict(result)
                
                # Parse metadata JSON
                if video.get('metadata'):
                    try:
                        video['metadata'] = json.loads(video['metadata'])
                    except json.JSONDecodeError:
                        pass
                
                videos.append(video)
            
            return videos
        finally:
            self._disconnect()