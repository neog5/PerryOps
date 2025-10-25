from typing import Optional, Dict, Any
from app.firebase_client import get_firestore_client
from app.schemas_firebase import User, LoginRequest, LoginResponse, UserRole
from datetime import datetime, timedelta
import jwt
import hashlib
import secrets

# Simple JWT secret (in production, use environment variable)
JWT_SECRET = "perryops-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

class AuthService:
    def __init__(self):
        self.db = get_firestore_client()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == hashed_password
    
    def create_access_token(self, user_id: str, email: str, role: UserRole) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role.value,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        # Find user by email
        users = self.db.collection("users").where("email", "==", email).stream()
        
        for user_doc in users:
            user_data = user_doc.to_dict()
            user_data["id"] = user_doc.id
            
            # Check password using hash verification
            stored_password = user_data.get("password")
            if stored_password and self.verify_password(password, stored_password):
                return User(**user_data)
        
        return None
    
    def login(self, login_request: LoginRequest) -> Optional[LoginResponse]:
        """Login user and return JWT token"""
        user = self.authenticate_user(login_request.email, login_request.password)
        
        if not user:
            return None
        
        # Create access token
        access_token = self.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role
        )
        
        return LoginResponse(
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            access_token=access_token
        )
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        # Get user from database
        user_doc = self.db.collection("users").document(user_id).get()
        if not user_doc.exists:
            return None
        
        user_data = user_doc.to_dict()
        user_data["id"] = user_doc.id
        return User(**user_data)
