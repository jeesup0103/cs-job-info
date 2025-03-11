from app.crawler.crawl import SkkuCrawler, SnuCrawler, YonseiCrawler, KaistCrawler

def run_all_crawlers():
    SkkuCrawler().crawl()
    SnuCrawler().crawl()
    YonseiCrawler().crawl()
    KaistCrawler().crawl()

if __name__ == "__main__":
    run_all_crawlers()