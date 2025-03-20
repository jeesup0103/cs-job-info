#!/bin/bash
while true; do
  echo "Starting crawler at $(date)"
  python -c "from app.crawler.run_crawlers import run_all_crawlers; run_all_crawlers()"
  echo "Crawler finished at $(date). Sleeping for 6 hours..."
  sleep 21600
done
