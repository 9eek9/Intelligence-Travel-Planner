from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    preferred_language: str = "en"

class LoginRequest(BaseModel):
    email: str