import asyncio
from app.shared.database import ArachneDB

class ArachneTrap:
    def __init__(self, host='0.0.0.0', port=2323):
        self.host = host
        self.port = port
        self.db = ArachneDB()

    async def handle_bot(self, reader, writer):
        ip, port = writer.get_extra_info('peername')
        print(f"Connection from {ip}:{port}")

        try:
            writer.write(b'\nlogin: ')
            await writer.drain()
            user_raw = await asyncio.wait_for(reader.read(100), timeout=10)
            username = user_raw.decode().strip()

            writer.write(b'\npassword: ')
            await writer.drain()
            pass_raw = await asyncio.wait_for(reader.read(100), timeout=10)

            password = pass_raw.decode().strip()
            print(f"Received credentials from {ip}:{port} - Username: {username}, Password: {password}")
            self.db.add_attack(ip, username=username, password=password)

        except asyncio.TimeoutError:
            print(f"Timeout for connection from {ip}:{port}")
        finally:
            writer.write(b'\nInvalid credentials. Connection closing.\n')
            writer.close()

    async def start(self):
        server = await asyncio.start_server(self.handle_bot, self.host, self.port)
        print(f"Honeytrap running on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()