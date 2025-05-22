from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlmodel import select, Session
from typing import Optional
from database import get_session, User ,ChatHistory
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import datetime as dt
from fastapi.background import BackgroundTask

from agent import agent,memory  # Import the agent from agent.py

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    native_language: str
    lang_code: str

class Query(BaseModel):
    query: str

# Dependency to validate API key
async def get_current_user(x_api_key: Optional[str] = Header(None), session: Session = Depends(get_session)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key is missing")
    user = session.exec(select(User).where(User.api_key == x_api_key)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user

# API Endpoints
@app.post("/register")
def register(user: UserCreate, session: Session = Depends(get_session)):
    """Register a new user with a username, password, and generate an API key."""
    existing_user = session.exec(select(User).where(User.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    password_hash = pwd_context.hash(user.password)
    new_user = User(username=user.username, password_hash=password_hash,
                    native_language=user.native_language, lang_code=user.lang_code)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)  # Refresh to get the generated api_key
    return {"message": "User registered successfully", "api_key": new_user.api_key}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """Authenticate a user and return their API key."""
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"api_key": user.api_key}

@app.post("/interact")
async def interact(query: Query, current_user: User = Depends(get_current_user)):
    """Interact with the English learning agent."""
    user_id = current_user.id
    session_id = f"{user_id}_session"
    agent.session_state['user_name'] = current_user.username
    agent.session_state['NATIVE_LANGUAGE'] = current_user.native_language
    agent.session_state['LANG_CODE'] = current_user.lang_code
    response = agent.run(query.query, user_id=str(user_id), session_id=session_id)
    return {"response": response.messages[-1].content}

@app.post("/stream")
async def interact(query: Query, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Interact with the English learning agent."""
    user_id = current_user.id
    session_id = f"{user_id}_session"
    agent.session_state['user_name'] = current_user.username
    agent.session_state['NATIVE_LANGUAGE'] = current_user.native_language
    agent.session_state['LANG_CODE'] = current_user.lang_code

    # add the user message to the agent's memory

    session.commit()

    def generate():
        run_response = agent.run(
            query.query, 
            user_id=str(user_id), 
            session_id=session_id,
            stream=True
        )
        for chunk in run_response:
            yield f"data: {chunk.content}\n\n"
    #add agent response to chat history
    
    return StreamingResponse(
        generate(), 
        media_type="text/event-stream")
       

@app.post("/chathistory")
async def get_chat_history(current_user: User = Depends(get_current_user)):
    """Get the chat history for the current user."""
    user_id = current_user.id
    session_id = f"{user_id}_session"
    chat_history = memory.get_user_memories(user_id=str(user_id))
    return {"chat_history": chat_history}