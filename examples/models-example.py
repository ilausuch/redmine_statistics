import sys
sys.path.append("..")

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from models import Issue, Issue_State, Base

engine = create_engine('sqlite:///example.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

issue = Issue(issue_id="1", project_id="1")
session.add(issue)

issue_state = Issue_State(issue_id="1", created_on=datetime.now(), field="state", new_value="In progress")
session.add(issue_state)

session.commit()
