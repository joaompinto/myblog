# db.py
from sqlmodel import Field, SQLModel, Session, create_engine, PrimaryKeyConstraint, select


import bcrypt

# SQLite database URL
sqlite_url = "sqlite:///editor_content.db"

# Create a SQLite database engine
engine = create_engine(sqlite_url)

# Define a SQLModel model for the editor content
class EditorContent(SQLModel, table=True):
    content_id: int = Field(default=None, primary_key=True)
    author_id: int = Field(default=None)
    content: str
    class Meta:
        constraints = [PrimaryKeyConstraint("content_id", "author_id")]
    #PrimaryKeyConstraint("content_id", "author_id")

class Users(SQLModel, table=True):
    author_id: int = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    name: str = Field(default="John Doe")
    password: str

    def hash_password(self):
        self.password = bcrypt.hashpw(self.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

# Create the tables if they don't exist
SQLModel.metadata.create_all(engine)

# Dependency to get the database session
def get_session():
    with Session(engine) as session:
        yield session

def get_user_by_email(email: str):
    with Session(engine) as session:
        statement = select(Users).where(Users.email == email)
        user = session.exec(statement).first()
        if user:
            return user.name, user.author_id
        return None