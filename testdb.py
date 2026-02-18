from apps.shared.database import ArachneDB
from apps.workers.enricher import GeoEnricher

db = ArachneDB()
if False:
    db.insert_attack({
        "ip_address": "192.168.1.1",
        "username": "admin",
        "password": "secret",
        "city": "New York",
        "country": "USA",
        "latitude": 40.7128,
        "longitude": -74.0060
    })
if False:
    print(db.get_pending_enrich())

# print(db.get_enriched())

ge = GeoEnricher()
if True:
    ge.enrich_db()