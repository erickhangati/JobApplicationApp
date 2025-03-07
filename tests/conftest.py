import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from database import Base, get_db
from main import app
from models import Users
from routers.auth import bcrypt_context, get_current_user

load_dotenv()

TEST_DB_URL = os.getenv("TEST_DB_URL")

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False},
                       poolclass=StaticPool)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestSessionLocal()

    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {
        "id": 1,
        "username": "test_user",
        "role": "ADMIN"
    }


@pytest.fixture
def test_user():
    user = Users(
        first_name="Jane",
        last_name="Doe",
        email="janedoe@mail.com",
        username="jane_doe",
        hashed_password=bcrypt_context.hash("test1234"),
        role="ADMIN"
    )

    db = TestSessionLocal()
    db.add(user)
    db.commit()
    yield db

    with engine.connect() as connection:
        connection.execute(text('DELETE FROM users'))
        connection.commit()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)
