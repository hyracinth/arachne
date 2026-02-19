import os
import ipaddress
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

class ArachneDB:
    FIELD_LIMITS = {
        "default": 255,
        "notes": 1024,
    }

    def __init__(self):
        self.conn_url = os.getenv("DATABASE_URL")
        self._client = None

    def _get_conn(self):
        if self._client is None or self._client.closed:
            print("*** Connecting to Supabase ***")
            conn = psycopg2.connect(self.conn_url)
            with conn.cursor() as cur:
                # Set search path to schema
                cur.execute("SET search_path TO arachne, public")
            self._client = conn
        return self._client

    def validate_ip(self, ip):
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def clean_string(self, fieldname, data):
        if data is None:
            return ""
        limit = self.FIELD_LIMITS.get(fieldname, self.FIELD_LIMITS["default"])
        return data.replace('\x00', '')[:limit].strip()

    def clean_input_dict(self, raw_dict, check_ip=True):
        clean_data = {}
        ip = raw_dict.get('ip_address')
        if check_ip:
            if self.validate_ip(ip):
                clean_data['ip_address'] = ip
            else:
                raise ValueError(f'Invalid IP address: {ip}')

        for key, value in raw_dict.items():
            if key == 'ip_address':
                continue          
            elif isinstance(value, str):
                clean_data[key] = self.clean_string(key, value)
            else:
                clean_data[key] = value
        return clean_data

    def insert_attack(self, raw_data):
        clean_data = self.clean_input_dict(raw_data)
        columns = clean_data.keys()
        values = [clean_data[col] for col in columns]
        placeholders = ["%s"] * len(values)

        query = f'''
                 INSERT INTO arachne.attacks ({', '.join(columns)})
                 VALUES ({', '.join(placeholders)})
                 '''
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                conn.commit()
        except Exception as e:
            print(f'[DEBUG] Failed to insert into attack: {e}')

    def update_attack(self, id, raw_data):
        clean_data = self.clean_input_dict(raw_data, False)

        columns = raw_data.keys()
        set_clause = ", ".join([f"{col} = %s" for col in columns])
        values = [clean_data[col] for col in columns]

        query = f'''
                 UPDATE arachne.attacks
                 SET {set_clause} WHERE id = %s
                 '''
        values.append(id)
        # TODO Check to see if anything's null, don't want to show null

        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
            print(f'[DEBUG] Updated attack {id} with {clean_data}')
        except Exception as e:
            print(f'[DEBUG] Failed to update attack {id}: {e}')

    def get_pending_enrich(self, limit=30):
        query = f'SELECT id, ip_address FROM arachne.attacks WHERE city is NULL LIMIT %s'
        conn = self._get_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (limit,))
            return cur.fetchall()
        
    def get_enriched(self, limit=100):
        query = f'''
                 SELECT timestamp, ip_address, username, password, city, country, latitude, longitude
                 FROM arachne.attacks 
                 WHERE city is NOT NULL 
                 ORDER BY timestamp DESC 
                 LIMIT %s
                 '''
        conn = self._get_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (limit,))
            return cur.fetchall()