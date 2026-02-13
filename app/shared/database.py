import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

class ArachneDB:
    def __init__(self):
        self.conn_url = os.getenv("DATABASE_URL")

    def _get_conn(self):
        conn = psycopg2.connect(self.conn_url)
        with conn.cursor() as cur:
            # Set search path to schema
            cur.execute("SET search_path TO arachne, public")
        return conn
    
    def add_attack(self, ip, user=None, password=None, city=None, country=None, latitude=None, longitude=None):
        query = f"""
            INSERT INTO attacks (ip_address, username, password, city, country, latitude, longitude)
            VALUES ('{ip}', '{user}', '{password}', '{city}', '{country}', '{latitude}', '{longitude}')
        """
        print(query)
        conn = self._get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(query)
            conn.commit()
