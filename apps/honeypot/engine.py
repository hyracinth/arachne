import time
import asyncio
from apps.shared.database import ArachneDB

class ArachneTrap:
    def __init__(self, host='0.0.0.0', ports=[2323], cooldown=60):
        self.host = host
        self.ports = ports
        self.cooldown = cooldown
        self.lastseen = {}
        self.db = ArachneDB()

    def is_allowed(self, ip):
        now = time.time()
        if ip in self.lastseen and now - self.lastseen[ip] < self.cooldown:
            return False
        self.lastseen[ip] = now
        return True

    async def handle_bot(self, reader, writer):
        ip, _ = writer.get_extra_info('peername')
        print(f"[*] Connection from {ip}")

        # Throttle repeated connections from the same IP
        if not self.is_allowed(ip):
            return

        # Initialize in case of timeout
        username, password = "TIMEOUT", "TIMEOUT"
        full_payload = None
        try:
            banner = (
                b"*************************************************************\n"
                b"* UNAUTHORIZED ACCESS TO THIS NETWORK DEVICE IS PROHIBITED. *\n"
                b"* ALL ACTIVITIES ARE MONITORED AND LOGGED.                  *\n"
                b"*************************************************************\n\n"
                b"Cisco IOS Software, C2900 Software (C2900-UNIVERSALK9-M)\n"
                b"Copyright (c) 1986-2018 by Cisco Systems, Inc.\n"
                b"User Access Verification\n"
            )
            writer.write(banner)
            writer.write(b'Username: ')
            await writer.drain()
            user_raw = await asyncio.wait_for(reader.read(1024), timeout=10)
            username = user_raw.decode(errors='ignore').strip() or ""

            if username.startswith(("GET", "POST", "HEAD")) or len(username) > 20:
                try:
                    raw_in = await asyncio.wait_for(reader.read(1024), timeout=10)
                    data_in = raw_in.decode(errors='ignore').strip() or ""
                except asyncio.TimeoutError:
                    data_in = ""
                full_payload = f"{username} {data_in}".strip()
                username = "HTTP_PAYLOAD"
                password = "HTTP_PAYLOAD"
            else:
                writer.write(b'\nPassword: ')
                await writer.drain()
                pass_raw = await asyncio.wait_for(reader.read(100), timeout=10)
                password = pass_raw.decode(errors='ignore').strip() or ""

        except asyncio.TimeoutError:
            print(f"Timeout for connection from {ip}")
        except Exception as e:
            print(f"Error handling connection from {ip}: {e}")
        finally:
            try:
                self.db.insert_attack({"ip_address": ip, 
                                       "username": username, 
                                       "password": password, 
                                       "notes": full_payload})
                print(f"Logged attack from {ip} with username '{username}' and password '{password}'")
            except Exception as e:
                print(f"Failed to log attack from {ip}: {e}")
            try:
                writer.write(b'\nInvalid credentials. Connection closing.\n')
                await writer.drain()
            except Exception as e:
                print(f"Failed to send response to {ip}: {e}")
                pass
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

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