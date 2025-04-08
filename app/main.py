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
from app.crawler.crawl import SkkuCrawler, SnuCrawler, YonseiCrawler, KaistCrawler, HanyangCrawler, run_all_skku_crawlers
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
async def root(
    request: Request,
    page: int = 1,
    school: str = None,
    db: Session = Depends(get_db)
):
    # Set items per page
    items_per_page = 9

    # Calculate offset
    offset = (page - 1) * items_per_page
    # Base query
    query = db.query(Notice)

    # Apply school filter if specified
    if school:
        query = query.filter(Notice.source_school == school)

    # Get total count of notices
    total_notices = query.count()

    notices = query.order_by(Notice.date_posted.desc()).offset(offset).limit(items_per_page).all()

    # Calculate total pages
    total_pages = (total_notices + items_per_page - 1) // items_per_page

    schools = ["성균관대학교", "연세대학교", "카이스트"]  # Add all your schools here
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notices": notices,
            "schools": schools,
            "selected_school": school,
            "current_page": page,
            "total_pages": total_pages
        }
    )

@app.get("/search", response_class=HTMLResponse)
async def search_notices(request: Request, q: str, page: int = 1, db: Session = Depends(get_db)):
    # Set items per page
    items_per_page = 9

    # Calculate offset
    offset = (page - 1) * items_per_page

    # Get total count of matching notices
    total_notices = db.query(Notice).filter(
        (Notice.title.ilike(f"%{q}%")) |
        (Notice.content.ilike(f"%{q}%"))
    ).count()

    # Get paginated notices
    notices = db.query(Notice).filter(
        (Notice.title.ilike(f"%{q}%")) |
        (Notice.content.ilike(f"%{q}%"))
    ).order_by(Notice.date_posted.desc())\
    .offset(offset).limit(items_per_page).all()

    # Calculate total pages
    total_pages = (total_notices + items_per_page - 1) // items_per_page

    schools = ["성균관대학교", "연세대학교", "카이스트"]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notices": notices,
            "schools": schools,
            "current_page": page,
            "total_pages": total_pages,
            "search_query": q
        }
    )

# API endpoints
@app.get("/api/notices")
def get_notices(request: Request, db: Session = Depends(get_db)):
    notices = db.query(Notice).all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notices": notices,
            "current_page": 1,
            "total_pages": 1,
            "schools": ["성균관대학교", "연세대학교", "카이스트"]
        }
    )

@app.post("/api/insert_notice")
def post_notice(notice_req: NoticeRequestCreate, db: Session = Depends(get_db)):
    try:
        return add_notice(db, notice_req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Crawler endpoints
@app.get("/skku")
def skku(request: Request):
    notices = run_all_skku_crawlers()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notices": notices,
            "current_page": 1,
            "total_pages": 1,
            "schools": ["성균관대학교"]
        }
    )


# @app.get("/snu")
# def snu(request: Request):
#     crawler = SnuCrawler()
#     notices = crawler.crawl()
#     return templates.TemplateResponse(
#         "index.html",
#         {
#             "request": request,
#             "notices": notices,
#             "current_page": 1,
#             "total_pages": 1,
#             "schools": ["성균관대학교", "연세대학교", "카이스트"]
#         }
#     )

@app.get("/yonsei")
def yonsei(request: Request):
    crawler = YonseiCrawler()
    notices = crawler.crawl()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notices": notices,
            "current_page": 1,
            "total_pages": 1,
            "schools": ["연세대학교"]
        }
    )

@app.get("/kaist")
def kaist(request: Request):
    crawler = KaistCrawler()
    notices = crawler.crawl()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notices": notices,
            "current_page": 1,
            "total_pages": 1,
            "schools": ["카이스트"]
        }
    )