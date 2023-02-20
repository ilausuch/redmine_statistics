from sqlalchemy import Column,  Integer, String, Date, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.orm import declarative_base, mapped_column

Base = declarative_base()

class Issue(Base):
    __tablename__ = 'issue'
    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(String)
    project_id = Column(String)
    project_name = Column(String)
    type_id = Column(String)
    type_name = Column(String)
    status_id = Column(String)
    status_name = Column(String)
    priority_id = Column(String)
    priority_name = Column(String)
    author_id = Column(String)
    author_name = Column(String)
    assigned_to_id = Column(String)
    assigned_to_name = Column(String)
    subject = Column(String)
    start_date = Column(DateTime)
    due_date = Column(DateTime)
    estimated_hours = Column(Integer)
    created_on = Column(DateTime)
    updated_on = Column(DateTime)
    closed_on = Column(DateTime)
    __table_args__ = (UniqueConstraint('issue_id', 'project_id', name='_unique_key'),)

class Issue_State(Base):
    __tablename__ = 'issue_state'
    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = mapped_column(ForeignKey("issue.issue_id"))
    user_id = Column(String)
    user_name = Column(String)
    created_on = Column(DateTime)
    field = Column(String)
    old_value = Column(String)
    new_value = Column(String)
    __table_args__ = (UniqueConstraint('issue_id', 'created_on', name='_unique_key'),)
