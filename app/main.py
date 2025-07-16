from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.db.session import engine, SessionLocal
from app.db.models import Base, Notice
from app.crawler.crawl import SkkuCrawler, SnuCrawler, YonseiCrawler, KaistCrawler, run_all_skku_crawlers, ChromeDriverManager
from app.db.schemas import NoticeRequestCreate
from app.db.crud import add_notice

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHOOLS = ["성균관대학교", "연세대학교", "카이스트", "서울대학교"]
ITEMS_PER_PAGE = 9

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_paginated_notices(db: Session, page: int, school: str = None, search_query: str = None):
    """Get paginated notices with optional filtering"""
    offset = (page - 1) * ITEMS_PER_PAGE
    query = db.query(Notice)

    if school:
        query = query.filter(Notice.source_school == school)

    if search_query:
        query = query.filter(
            (Notice.title.ilike(f"%{search_query}%")) |
            (Notice.content.ilike(f"%{search_query}%"))
        )

    total_notices = query.count()
    notices = query.order_by(Notice.date_posted.desc()).offset(offset).limit(ITEMS_PER_PAGE).all()
    total_pages = (total_notices + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    return notices, total_pages

def render_notices_template(request: Request, notices, current_page: int, total_pages: int,
                          selected_school: str = None, search_query: str = None):
    """Render notices template with common context"""
    context = {
        "request": request,
        "notices": notices,
        "schools": SCHOOLS,
        "current_page": current_page,
        "total_pages": total_pages
    }

    if selected_school:
        context["selected_school"] = selected_school
    if search_query:
        context["search_query"] = search_query

    return templates.TemplateResponse("index.html", context)

# App setup
app = FastAPI()
create_tables()

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, page: int = 1, school: str = None, db: Session = Depends(get_db)):
    notices, total_pages = get_paginated_notices(db, page, school)
    return render_notices_template(request, notices, page, total_pages, school)

@app.get("/search", response_class=HTMLResponse)
async def search_notices(request: Request, q: str, page: int = 1, db: Session = Depends(get_db)):
    notices, total_pages = get_paginated_notices(db, page, search_query=q)
    return render_notices_template(request, notices, page, total_pages, search_query=q)

@app.get("/api/notices")
def get_notices(request: Request, db: Session = Depends(get_db)):
    notices = db.query(Notice).all()
    return render_notices_template(request, notices, 1, 1)

@app.post("/api/insert_notice")
def post_notice(notice_req: NoticeRequestCreate, db: Session = Depends(get_db)):
    try:
        return add_notice(db, notice_req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_crawler_endpoint(request: Request, crawler_func, school_name: str):
    """Generic crawler endpoint handler"""
    driver_manager = ChromeDriverManager()
    driver = driver_manager.create_driver()
    try:
        notices = crawler_func(driver)
        return render_notices_template(request, notices, 1, 1, school_name)
    finally:
        driver_manager.quit()

@app.get("/skku")
def skku(request: Request):
    return run_crawler_endpoint(request, run_all_skku_crawlers, "성균관대학교")

@app.get("/snu")
def snu(request: Request):
    crawler = SnuCrawler()
    notices = crawler.crawl()
    return render_notices_template(request, notices, 1, 1, "서울대학교")

@app.get("/yonsei")
def yonsei(request: Request):
    def crawl_yonsei(driver):
        crawler = YonseiCrawler(driver=driver)
        return crawler.crawl()
    return run_crawler_endpoint(request, crawl_yonsei, "연세대학교")

@app.get("/kaist")
def kaist(request: Request):
    def crawl_kaist(driver):
        crawler = KaistCrawler(driver=driver)
        return crawler.crawl()
    return run_crawler_endpoint(request, crawl_kaist, "카이스트")