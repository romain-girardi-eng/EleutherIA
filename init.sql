-- Initialization script for Ancient Free Will Database PostgreSQL setup
-- This script creates the basic database structure

-- Create the free_will schema
CREATE SCHEMA IF NOT EXISTS free_will;

-- Grant permissions to the free_will_user
GRANT ALL PRIVILEGES ON SCHEMA free_will TO free_will_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA free_will TO free_will_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA free_will TO free_will_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA free_will GRANT ALL ON TABLES TO free_will_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA free_will GRANT ALL ON SEQUENCES TO free_will_user;

-- Create a simple table to test the setup
CREATE TABLE IF NOT EXISTS free_will.setup_log (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial log entry
INSERT INTO free_will.setup_log (message) VALUES ('Database initialized successfully');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_setup_log_created_at ON free_will.setup_log(created_at);
