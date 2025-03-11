from fastapi import FastAPI, Depends, Request, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os

from app.db.session import engine
from app.db.models import Base, Notice
from app.db.session import SessionLocal
from app.crawler.crawl import SkkuCrawler, SnuCrawler, YonseiCrawler, KaistCrawler
from app.db.schemas import NoticeRequest, NoticeRequestCreate
from app.db.crud import add_notice, get_notice_by_link

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_application():
    app = FastAPI()
    create_tables()
    return app

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = get_application()

# Get the absolute path to the app directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    notices = db.query(Notice).order_by(Notice.date_posted.desc()).all()
    schools = ["SKKU", "SNU", "Yonsei"]  # You might want to make this dynamic
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "notices": notices, "schools": schools}
    )

@app.get("/school/{school_name}", response_class=HTMLResponse)
async def school_notices(request: Request, school_name: str, db: Session = Depends(get_db)):
    notices = db.query(Notice).filter(Notice.source_school == school_name).order_by(Notice.date_posted.desc()).all()
    schools = ["SKKU", "SNU", "Yonsei"]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "notices": notices, "schools": schools}
    )

@app.get("/search", response_class=HTMLResponse)
async def search_notices(request: Request, q: str, db: Session = Depends(get_db)):
    notices = db.query(Notice).filter(
        (Notice.title.ilike(f"%{q}%")) |
        (Notice.content.ilike(f"%{q}%"))
    ).order_by(Notice.date_posted.desc()).all()
    schools = ["SKKU", "SNU", "Yonsei"]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "notices": notices, "schools": schools}
    )

# API endpoints
@app.get("/api/notices")
def get_notices(db: Session = Depends(get_db)):
    return db.query(Notice).all()

@app.post("/api/insert_notice")
def post_notice(notice_req: NoticeRequestCreate, db: Session = Depends(get_db)):
    try:
        return add_notice(db, notice_req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Crawler endpoints
@app.get("/skku")
def skku():
    crawler = SkkuCrawler()
    return crawler.crawl()

@app.get("/snu")
def snu():
    crawler = SnuCrawler()
    return crawler.crawl()

@app.get("/yonsei")
def yonsei():
    crawler = YonseiCrawler()
    return crawler.crawl()

@app.get("/kaist")
def kaist():
    crawler = KaistCrawler()
    return crawler.crawl()