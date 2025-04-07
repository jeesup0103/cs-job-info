# CS Job Info

A web application that displays job notices from Computer Science departments of different universities.

## Technology Stack

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

### Frontend
- **Bootstrap 5**: Frontend CSS framework
  - Responsive grid system
  - Pre-built components
  - Modern UI design

- **Jinja2**: Template engine for Python
  - Server-side rendering of HTML
  - Template inheritance and reusability
  - Dynamic content generation

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

- **Nginx**: Web server and reverse proxy
  - Serves static files
  - Load balancing
  - SSL/TLS termination
  - Reverse proxy to FastAPI application

### Crawling/Scraping
- **BeautifulSoup4**: Web scraping library
  - HTML parsing
  - Data extraction from university websites
  - Clean and maintainable scraping code

## Project Structure
```
.
├── app/
│   ├── crawler/      # Web crawlers for different universities
│   ├── db/           # Database models and operations
│   ├── static/       # Static files (CSS)
│   ├── templates/    # Jinja2 HTML templates
│   └── main.py       # FastAPI application entry point
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Features
- Aggregates notices from multiple university CS departments
- Real-time search functionality
- Pagination for better user experience
- Responsive design for mobile and desktop
- Automated crawling every 6 hours