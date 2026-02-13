import asyncio
from app.shared.database import ArachneDB

class ArachneTrap:
    def __init__(self, host='0.0.0.0', ports=[2323]):
        self.host = host
        self.ports = ports
        self.db = ArachneDB()

    async def handle_bot(self, reader, writer):
        ip, port = writer.get_extra_info('peername')
        print(f"Connection from {ip}:{port}")
        # Initialize in case of timeout
        username, password = "TIMEOUT", "TIMEOUT"
        try:
            writer.write(b'Cisco IOS Software, C2900 Software (C2900-UNIVERSALK9-M)\n')
            writer.write(b'Copyright (c) 1986-2018 by Cisco Systems, Inc.\n')
            writer.write(b'User Access Verification\n\n')
            writer.write(b'Username: ')
            await writer.drain()
            user_raw = await asyncio.wait_for(reader.read(100), timeout=10)
            username = user_raw.decode().strip() or ""

            writer.write(b'\nPassword: ')
            await writer.drain()
            pass_raw = await asyncio.wait_for(reader.read(100), timeout=10)

            password = pass_raw.decode().strip() or ""

        except asyncio.TimeoutError:
            print(f"Timeout for connection from {ip}:{port}")
        except Exception as e:
            print(f"Error handling connection from {ip}:{port}: {e}")
        finally:
            self.db.add_attack(ip, username=username, password=password)
            try:
                writer.write(b'\nInvalid credentials. Connection closing.\n')
                await writer.drain()
            except:
                pass
            writer.close()
            await writer.wait_closed()

    async def start(self):
        servers = []
        for port in self.ports:
            try:
                server = await asyncio.start_server(self.handle_bot, self.host, port)
                print(f"Honeytrap running on {self.host}:{port}")
                servers.append(server.serve_forever())
            except Exception as e:
                print(f"Failed to start server on port {port}: {e}")
        
        if servers:
            await asyncio.gather(*servers)