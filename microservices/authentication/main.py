from fastapi import FastAPI, APIRouter, Depends, HTTPException, Response
from uuid import uuid4
from shared.database import users_collection
from shared.session_manager import SessionData, backend, cookie, authenticate_user
from pydantic import BaseModel

class UserSignup(BaseModel):
    username: str
    password: str

router = APIRouter()
app = FastAPI()

# Signup endpoint
@router.post("/signup")
async def signup(user: UserSignup):
    existing_user = users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    users_collection.insert_one({"username": user.username, "password": user.password})
    return {"message": "User created successfully"}

# Login endpoint
@router.post("/login")
async def login(response: Response, user: dict = Depends(authenticate_user)):
    session = uuid4()
    data = SessionData(username=user["username"])
    await backend.create(session, data)
    cookie.attach_to_response(response, session)
    return {"message": f"Session created for {user['username']}"}

app.include_router(router)