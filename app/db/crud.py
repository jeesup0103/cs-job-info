from sqlalchemy.orm import Session

from db.models import Notice
from db.schemas import NoticeRequest


def add_notice(db: Session, data: NoticeRequest) -> Notice:
    new_notice = Notice(
        title=data.title,
        content=data.content,
        original_link=data.original_link,
        date_posted=data.date_posted,
        source_school=data.source_school
    )    
    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    
    db.query(Notice).all()