# CS Job Notices

A web application that aggregates and displays job notices from various Computer Science departments of different universities.

## Technology Stack

### Frontend
- **Bootstrap 5**: Frontend CSS framework
  - Responsive grid system
  - Pre-built components
  - Modern UI design

- **Jinja2**: Template engine for Python
  - Server-side rendering of HTML
  - Template inheritance and reusability
  - Dynamic content generation

### Backend
- **FastAPI**: Modern, fast web framework for building APIs with Python
  - High performance, easy to use, and automatic API documentation
  - Used for handling HTTP requests and serving the web application
  - Async support for better performance

- **SQLAlchemy**: SQL toolkit and ORM
  - Database model definitions and relationships
  - Database migrations and schema management
  - Used for all database operations

- **PyMySQL**: MySQL client library for Python
  - Database connector for MySQL
  - Used for establishing connections with the MySQL database

### Database
- **MySQL**: Relational database
  - Stores all notice data
  - Maintains data consistency and relationships
  - Efficient querying and indexing

### Infrastructure
- **Docker**: Containerization platform
  - Application containerization
  - Development and production environment consistency
  - Easy deployment and scaling

- **Docker Compose**: Multi-container Docker applications
  - Service orchestration
  - Environment variable management
  - Container networking

- **Nginx (nginx-proxy with Let’s Encrypt companion)**: Web server and reverse proxy
  - Reverse Proxy: Routes incoming requests to the appropriate FastAPI application container based on domain
  - SSL/TLS Termination: Automatically obtains and renews SSL certificates from Let’s Encrypt via the acme-companion container
  - Dynamic Configuration: Uses docker-gen to dynamically update its configuration as containers start and stop
  - Static File Serving & Load Balancing: Optionally serves static content and can distribute traffic if scaling out services

### Crawling/Scraping

- **Selenium with Chrome WebDriver**: Browser automation tool
  - Handles dynamic JavaScript content
  - Enables interaction with modern web applications
  - Required for websites that load content dynamically (SPA, AJAX)
  - Simulates real browser behavior for reliable scraping

## Project Structure
```
.
├── app/
│   ├── crawler/      # Web crawlers for different universities
│   ├── db/           # Database models and operations
│   ├── static/       # Static files (CSS, JS)
│   ├── templates/    # Jinja2 HTML templates
│   └── main.py       # FastAPI application entry point
├── nginx_conf
│   ├── default.conf
├── docker-compose.yml
├── Dockerfile
└──  requirements.txt
```

## Features
- Aggregates job notices from multiple university CS departments
- Real-time search functionality
- Pagination for better user experience
- Responsive design for mobile and desktop
- Automated crawling every 24 hours