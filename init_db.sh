#!/bin/bash
set -e

echo "Waiting for MySQL to be ready..."
while ! mysqladmin ping -h"db" -u"root" -p"1234" --silent; do
    sleep 1
done
echo "MySQL is ready!"

echo "Creating database and tables..."
mysql -h db -u root -p1234 -e "CREATE DATABASE IF NOT EXISTS notice_db;"
mysql -h db -u root -p1234 notice_db -e "CREATE TABLE IF NOT EXISTS notices (
    notice_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    original_link VARCHAR(255) UNIQUE,
    date_posted VARCHAR(100),
    source_school VARCHAR(100)
);"
echo "Database and tables created successfully!"