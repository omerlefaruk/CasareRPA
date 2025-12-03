-- Create database
CREATE DATABASE casare_rpa;

-- Create user
CREATE USER casare_user WITH PASSWORD 'postgre';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE casare_rpa TO casare_user;
