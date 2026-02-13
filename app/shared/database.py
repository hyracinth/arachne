import os
import ipaddress
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def validate_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def clean_input(data, max_len=255):
    if data is None:
        return ""
    data = data[:max_len]
    return data.strip()

class ArachneDB:
    def __init__(self):
        self.conn_url = os.getenv("DATABASE_URL")

    def _get_conn(self):
        conn = psycopg2.connect(self.conn_url)
        with conn.cursor() as cur:
            # Set search path to schema
            cur.execute("SET search_path TO arachne, public")
        return conn

    def add_attack(self, ip, username=None, password=None, city=None, country=None, latitude=None, longitude=None, notes=None):
        if not validate_ip(ip):
            raise ValueError(f"Invalid IP address: {ip}")
        
        # TODO find better way to do this?
        username = clean_input(username)
        password = clean_input(password)
        city = clean_input(city)
        country = clean_input(country)
        notes = clean_input(notes, 1024)

        # Use parameterized query to prevent SQL injection
        query = """
                INSERT INTO attacks (ip_address, username, password, city, country, latitude, longitude, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

        conn = self._get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, (ip, username, password, city, country, latitude, longitude, notes))
            conn.commit()
