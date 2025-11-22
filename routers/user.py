from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User
from models.schemas_user import UserCreate
import uuid

router = APIRouter()

@router.post("/create")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        id=uuid.uuid4(),
        email=user.email,
        name=user.name,
        preferred_language=user.preferred_language
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user_id": str(new_user.id),
        "email": new_user.email,
        "name": new_user.name,
        "preferred_language": new_user.preferred_language
    }
