from fastapi import FastAPI, Depends, Request, HTTPException, Response, UploadFile, File, Form
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List

from db.session import engine
from db.models import Base
from db.session import SessionLocal
from crawler.crawl import SkkuCrawler
from db.schemas import  NoticeRequest, NoticeRequestCreate
from db.crud import add_notice


def create_tables():
    Base.metadata.create_all(bind=engine)
def get_application():
    app=FastAPI()
    create_tables()
    return app
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = get_application()

@app.get("/")
async def root():
    return {"message":"Hello"}

@app.get("/skku")
def skku():
    crawler = SkkuCrawler()
    return crawler.crawl()

@app.post("/api/insert_notice")
def post_notice(notice_req: NoticeRequestCreate, db: Session = Depends(get_db)):
    try:
        return add_notice(db, notice_req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))