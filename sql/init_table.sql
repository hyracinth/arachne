-- 1. Create the custom schema
CREATE SCHEMA IF NOT EXISTS arachne;

-- 2. Create the table inside that schema
CREATE TABLE arachne.attacks (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    ip_address TEXT NOT NULL,
    username TEXT,
    password TEXT,
    city TEXT,
    country TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);