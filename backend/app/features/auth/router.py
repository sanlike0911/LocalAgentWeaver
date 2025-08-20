from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.features.auth.schemas import UserCreate, UserLogin, User, Token
from app.features.auth.service import AuthService
from app.features.auth.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    return await AuthService.create_user(db, user_data)


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login user and return access token"""
    user = await AuthService.authenticate_user(db, user_data)
    return AuthService.create_token(user)


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user