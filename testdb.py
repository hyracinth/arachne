from app.shared.database import ArachneDB

db = ArachneDB()

db.insert_attack({
    "ip_address": "192.168.1.1",
    "username": "admin",
    "password": "secret",
    "city": "New York",
    "country": "USA",
    "latitude": 40.7128,
    "longitude": -74.0060
})
