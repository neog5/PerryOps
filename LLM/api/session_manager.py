"""
Session management for tracking processing state.
"""

import os
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class SessionManager:
    """Manages processing sessions and their state."""
    
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def create_session(self) -> str:
        """
        Create a new session and return its ID.
        
        Returns:
            str: Unique session ID
        """
        session_id = str(uuid.uuid4())
        session_dir = self.base_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Create session metadata
        metadata = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "created"
        }
        
        self._save_metadata(session_id, metadata)
        return session_id
    
    def get_session_dir(self, session_id: str) -> Path:
        """Get the directory path for a session."""
        return self.base_dir / session_id
    
    def save_file(self, session_id: str, filename: str, content: bytes) -> Path:
        """
        Save an uploaded file to the session directory.
        
        Args:
            session_id: Session identifier
            filename: Name of the file
            content: File content as bytes
            
        Returns:
            Path: Path to the saved file
        """
        session_dir = self.get_session_dir(session_id)
        file_path = session_dir / filename
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path
    
    def save_data(self, session_id: str, key: str, data: Any) -> None:
        """
        Save data to the session.
        
        Args:
            session_id: Session identifier
            key: Data key (e.g., 'structured_data', 'compliance_report')
            data: Data to save (must be JSON-serializable)
        """
        session_dir = self.get_session_dir(session_id)
        data_file = session_dir / f"{key}.json"
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_data(self, session_id: str, key: str) -> Optional[Any]:
        """
        Load data from the session.
        
        Args:
            session_id: Session identifier
            key: Data key
            
        Returns:
            Data if exists, None otherwise
        """
        session_dir = self.get_session_dir(session_id)
        data_file = session_dir / f"{key}.json"
        
        if not data_file.exists():
            return None
        
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_status(self, session_id: str, status: str) -> None:
        """Update the session status."""
        metadata = self._load_metadata(session_id)
        metadata["status"] = status
        metadata["updated_at"] = datetime.utcnow().isoformat()
        self._save_metadata(session_id, metadata)
    
    def _save_metadata(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """Save session metadata."""
        session_dir = self.get_session_dir(session_id)
        metadata_file = session_dir / "metadata.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def _load_metadata(self, session_id: str) -> Dict[str, Any]:
        """Load session metadata."""
        session_dir = self.get_session_dir(session_id)
        metadata_file = session_dir / "metadata.json"
        
        if not metadata_file.exists():
            return {"session_id": session_id}
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self.get_session_dir(session_id).exists()
    
    def get_file_path(self, session_id: str, filename: str) -> Optional[Path]:
        """
        Get the path to a file in the session.
        
        Returns:
            Path if file exists, None otherwise
        """
        file_path = self.get_session_dir(session_id) / filename
        return file_path if file_path.exists() else None
