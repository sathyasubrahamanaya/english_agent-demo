from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional, Generator
import uuid

# Database configuration
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Create the database engine
engine = create_engine(sqlite_url, echo=True)

# Define the User model with api_key
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password_hash: str
    native_language: str
    lang_code: str
    # The api_key is generated automatically and is unique
    api_key: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)

class ChatHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    session_id: str
    role: str
    content: str = Field(default="")
    timestamp: str = Field(default_factory=lambda: str(uuid.uuid4()))
    input_token_count: int = Field(default=0)
    output_token_count: int = Field(default=0)

# Dependency to get a database session
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

# Create the database tables
SQLModel.metadata.create_all(engine)