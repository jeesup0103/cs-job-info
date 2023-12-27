from pydantic import BaseModel
from typing import Optional
from datetime import date

class NoticeRequestBase(BaseModel):
    notice_id: Optional[int]
    title: str
    content: str
    original_link: str
    date_posted: date
    source_school: str

class NoticeRequestCreate(NoticeRequestBase):
    pass

class NoticeRequest(NoticeRequestBase):
    id: Optional[int]

    class Config:
        orm_mode = True