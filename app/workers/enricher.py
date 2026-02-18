import requests
import time
from app.shared.database import ArachneDB

class GeoEnricher:
    def __init__(self):
        self.seen_ips = {}
        self.db = ArachneDB()
        self.headers = {
            'User-Agent': 'Arachne/1.0'
        }

    def get_geo_data(self, ip):
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}', headers=self.headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get('status').lower() == 'success':
                return {
                    "city": data.get("city"),
                    "country": data.get("country"),
                    "latitude": data.get("lat"),
                    "longitude": data.get("lon"),
                }
            else:
                print(f'IP-API could not locate {ip}: {data.get('message')}')
        except Exception as e:
            print(f'Error connecting to IP-API: {e}')
            return None

    def enrich_db(self):
        while True:
            if len(self.seen_ips) > 1000: 
                self.seen_ips.clear()

            curr_batch = self.db.get_pending_enrich(1)
            if len(curr_batch) == 0:
                return

            for curr_record in curr_batch:
                called_api = False
                id = curr_record['id']
                ip = curr_record['ip_address']
                print(f"Processing {id} {ip}" )

                if not ip in self.seen_ips:
                    called_api = True
                    geo_data = self.get_geo_data(ip)
                    self.seen_ips[ip] = geo_data
                else:
                    geo_data = self.seen_ips[ip]

                if geo_data:
                    self.db.update_attack(id, geo_data)

                # Rate limit
                # TODO switch to bulk or find better way
                if called_api:
                    time.sleep(1.5)

            # Just run one iteration for now
            return