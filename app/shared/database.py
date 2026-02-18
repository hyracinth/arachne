import os
import ipaddress
from dotenv import load_dotenv
import psycopg2

load_dotenv()

class ArachneDB:
    FIELD_LIMITS = {
        "default": 255,
        "notes": 1024,
    }

    def __init__(self):
        self.conn_key = os.getenv("DATABASE_KEY")
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
        return data[:limit].strip()

    def clean_input_dict(self, raw_dict):
        clean_data = {}
        ip = raw_dict.get('ip_address')
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
                    INSERT INTO attacks ({', '.join(columns)})
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