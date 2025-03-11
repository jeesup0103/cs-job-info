from sqlalchemy.orm import Session

from app.db.models import Notice
from app.db.schemas import NoticeRequest

def get_notice_by_link(db: Session, link: str):
    return db.query(Notice).filter(Notice.original_link == link).first()


def add_notice(db: Session, data: NoticeRequest):

    existing_notice = get_notice_by_link(db, data.original_link)
    if existing_notice:
        return False

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

    return db.query(Notice).all()