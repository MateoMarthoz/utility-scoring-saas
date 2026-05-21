from fastapi import FastAPI, APIRouter, Depends, HTTPException, Response
from shared.database import scores_collection
import torch
from load_model import load_model, load_process_sentences
from shared.session_manager import SessionData, verifier, cookie, backend, authenticate_user
from pydantic import BaseModel
from uuid import uuid4

class ScenarioInput(BaseModel):
    scenario: str

router = APIRouter()
app = FastAPI()

@router.post("/login")
async def login(response: Response, user: dict = Depends(authenticate_user)):
    session = uuid4()
    data = SessionData(username=user["username"])
    await backend.create(session, data)
    cookie.attach_to_response(response, session)
    return {"message": f"Session created for {user['username']}"}

@router.post("/utility_score", dependencies=[Depends(cookie)])
async def score(scenario_input: ScenarioInput, session_data: SessionData = Depends(verifier)):
    loaded_model = load_model()
    scenario = scenario_input.scenario
    loaded_model.eval()
    try:
        input_ids, input_mask = load_process_sentences([scenario])
        with torch.no_grad():
            output = loaded_model(input_ids, attention_mask=input_mask)[0]
        score = round(output.item(), 3)
        scores_collection.insert_one({"username": session_data.username, "scenario": scenario, "score": score})
        return {"Scenario": scenario, "Utility Score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")

app.include_router(router)
