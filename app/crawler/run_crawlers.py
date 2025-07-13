from app.crawler.crawl import SkkuCrawler, SnuCrawler, SkkuCrawler2, YonseiCrawler, KaistCrawler, HanyangCrawler ,ChromeDriverManager

def run_all_crawlers():
    # Create a single ChromeDriver instance to be shared across all crawlers
    driver_manager = ChromeDriverManager()
    driver = driver_manager.create_driver()

    try:
        # Initialize crawlers with the shared driver
        crawlers = [
            KaistCrawler(driver=driver),
            SkkuCrawler(driver=driver),
            SkkuCrawler2(driver=driver),
            SnuCrawler(driver=driver),
            YonseiCrawler(driver=driver),
            HanyangCrawler(driver=driver),
        ]

        # Run crawlers sequentially
        for crawler in crawlers:
            crawler.crawl()

    finally:
        # Clean up the driver
        driver_manager.quit()

if __name__ == "__main__":
    run_all_crawlers()