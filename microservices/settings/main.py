from fastapi import FastAPI, APIRouter, Depends, HTTPException, Response
from shared.database import users_collection, scores_collection
from shared.session_manager import SessionData, verifier, backend, cookie, authenticate_user
from schemas import list_serial
from uuid import uuid4
from pydantic import BaseModel

router = APIRouter()
app = FastAPI()

@router.post("/login")
async def login(response: Response, user: dict = Depends(authenticate_user)):
    session = uuid4()
    data = SessionData(username=user["username"])
    await backend.create(session, data)
    cookie.attach_to_response(response, session)
    return {"message": f"Session created for {user['username']}"}

# View history endpoint
@router.get("/history", dependencies=[Depends(cookie)])
async def view_history(session_data: SessionData = Depends(verifier)):
    history = list_serial(scores_collection.find({"username": session_data.username}))
    return {"history": history}

# Change password endpoint
@router.put("/change-password", dependencies=[Depends(cookie)])
async def change_password(new_password: str, session_data: SessionData = Depends(verifier)):
    result = users_collection.update_one({"username": session_data.username}, {"$set": {"password": new_password}})
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update password")
    return {"message": "Password updated successfully"}

# Delete account endpoint
@router.delete("/delete-account", dependencies=[Depends(cookie)])
async def delete_account(session_data: SessionData = Depends(verifier)):
    users_collection.delete_one({"username": session_data.username})
    scores_collection.delete_many({"username": session_data.username})
    return {"message": "Account and associated data deleted successfully"}

app.include_router(router)
