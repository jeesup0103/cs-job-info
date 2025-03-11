from pydantic import BaseModel, validator
from typing import Optional
from datetime import date, datetime

class NoticeRequestBase(BaseModel):
    title: str
    content: str
    original_link: str
    date_posted: str  # Changed to str to handle various date formats
    source_school: str
    notice_id: Optional[int] = None
    id: Optional[int] = None

    @validator('date_posted')
    def validate_date(cls, v):
        try:
            # Try different date formats
            for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%y.%m.%d', '%Y.%m.%d']:
                try:
                    return datetime.strptime(v, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
            raise ValueError(f"Date format not recognized: {v}")
        except Exception as e:
            raise ValueError(f"Invalid date format: {v}")

class NoticeRequestCreate(NoticeRequestBase):
    pass

class NoticeRequest(NoticeRequestBase):
    class Config:
        orm_mode = True

