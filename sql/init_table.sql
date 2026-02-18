CREATE SCHEMA IF NOT EXISTS arachne;

CREATE TABLE arachne.attacks (
  id SERIAL NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
  ip_address TEXT NOT NULL,
  username TEXT NULL,
  password TEXT NULL,
  city TEXT NULL,
  country TEXT NULL,
  latitude DOUBLE PRECISION NULL,
  longitude DOUBLE PRECISION NULL,
  notes TEXT NULL,
  CONSTRAINT attacks_pkey PRIMARY KEY (id)
)
