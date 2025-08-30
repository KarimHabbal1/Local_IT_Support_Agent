from app.db.session import engine
from app.db.models import Base, User
from sqlalchemy.orm import Session

# Create tables
Base.metadata.create_all(bind=engine)

# Seed demo users
with Session(engine) as session:
    if not session.query(User).count():
        session.add_all([
            User(username="alice"),
            User(username="bob")
        ])
        session.commit()
