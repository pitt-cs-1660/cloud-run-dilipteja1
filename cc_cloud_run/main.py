from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import firebase_admin
from google.cloud import firestore
from typing import Annotated
import datetime

app = FastAPI()

# mount static files
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
templates = Jinja2Templates(directory="/app/template")

# init firestore client
db = firestore.Client()
votes_collection = db.collection("votes")


@app.get("/")
async def read_root(request: Request):
    # stream all votes; count tabs / spaces votes, and get recent votes
    # votes = votes_collection.stream()
    # @note: we are storing the votes in `vote_data` list because the firestore stream closes after certain period of time
    votes = votes_collection.stream()
    if not votes:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "tabs_count": 0,
            "spaces_count": 0,
            "recent_votes": []
        })
    # store votes in a list
    vote_data = []
    for v in votes:
        vote_data.append(v.to_dict())
    # count tabs and spaces votes
    tabs_count = sum(1 for vote in vote_data if vote['team'] == 'TABS')
    spaces_count = sum(1 for vote in vote_data if vote['team'] == 'SPACES')

    # return the template with vote data
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tabs_count": tabs_count,
        "spaces_count": spaces_count,
        "recent_votes": vote_data
    })


@app.post("/")
async def create_vote(team: Annotated[str, Form()]):
    if team not in ["TABS", "SPACES"]:
        raise HTTPException(status_code=400, detail="Invalid vote")
    # create a new vote document in firestore
    votes_collection.add({
        "team": team,
        "time_cast": datetime.datetime.utcnow().isoformat()
    })
    return {"message": "Vote recorded successfully!", "team": team, 'ok': True}
