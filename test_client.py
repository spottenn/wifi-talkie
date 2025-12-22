#!/usr/bin/env python3
"""
Simulated M5Stack Atom Echo Walkie-Talkie Client

This script simulates an ESP32 device for testing the walkie-talkie system.
It can send and receive audio data (simulated), register with the server,
and simulate push-to-talk behavior.
"""

import asyncio
import json
import sys
import random
import websockets
from datetime import datetime

class SimulatedWalkieTalkie:
    def __init__(self, device_name, server_url):
        self.device_name = device_name
        self.server_url = server_url
        self.websocket = None
        self.is_transmitting = False
        self.received_audio_count = 0

    def log(self, message, level="INFO"):
        """Print formatted log message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        color_codes = {
            "INFO": "\033[94m",  # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",  # Red
            "AUDIO": "\033[95m",  # Magenta
        }
        reset = "\033[0m"
        color = color_codes.get(level, "")
        print(f"{color}[{timestamp}] [{self.device_name}] {level}: {message}{reset}")

    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.log(f"Connecting to {self.server_url}...")
            self.websocket = await websockets.connect(self.server_url)
            self.log("Connected to server!", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Connection failed: {e}", "ERROR")
            return False

    async def register(self):
        """Register device with server"""
        try:
            registration = {
                "type": "register",
                "device": self.device_name
            }
            await self.websocket.send(json.dumps(registration))
            self.log(f"Registered as '{self.device_name}'", "SUCCESS")
        except Exception as e:
            self.log(f"Registration failed: {e}", "ERROR")

    async def start_transmission(self):
        """Send start transmission message"""
        try:
            message = {"type": "start_transmission"}
            await self.websocket.send(json.dumps(message))
            self.is_transmitting = True
            self.log("Started transmission (PTT pressed)", "SUCCESS")
        except Exception as e:
            self.log(f"Failed to start transmission: {e}", "ERROR")

    async def end_transmission(self):
        """Send end transmission message"""
        try:
            message = {"type": "end_transmission"}
            await self.websocket.send(json.dumps(message))
            self.is_transmitting = False
            self.log("Ended transmission (PTT released)", "SUCCESS")
        except Exception as e:
            self.log(f"Failed to end transmission: {e}", "ERROR")

    async def send_audio(self, duration_ms=1000):
        """Simulate sending audio data"""
        try:
            # Simulate audio data (random bytes)
            # Real device would send int16 PCM samples at 16kHz
            sample_rate = 16000
            samples = int((sample_rate * duration_ms) / 1000)

            # Send audio in chunks (like the ESP32 would)
            chunk_size = 512  # AUDIO_BUFFER_SIZE
            total_bytes = samples * 2  # 16-bit = 2 bytes per sample

            for i in range(0, total_bytes, chunk_size):
                chunk = bytes([random.randint(0, 255) for _ in range(min(chunk_size, total_bytes - i))])
                await self.websocket.send(chunk)
                self.log(f"Sent audio chunk: {len(chunk)} bytes", "AUDIO")
                await asyncio.sleep(0.032)  # ~32ms between chunks (512 samples at 16kHz)

        except Exception as e:
            self.log(f"Failed to send audio: {e}", "ERROR")

    async def receive_messages(self):
        """Receive and handle messages from server"""
        try:
            async for message in self.websocket:
                if isinstance(message, bytes):
                    # Binary data = audio
                    self.received_audio_count += 1
                    self.log(f"Received audio data: {len(message)} bytes (total chunks: {self.received_audio_count})", "AUDIO")
                else:
                    # Text data = control messages
                    try:
                        data = json.loads(message)
                        msg_type = data.get('type', 'unknown')

                        if msg_type == 'welcome':
                            self.log(f"Server says: {data.get('message')}", "SUCCESS")
                            self.log(f"Connected clients: {data.get('clients', 'unknown')}", "INFO")
                        elif msg_type == 'registered':
                            self.log(f"Registration confirmed. Total clients: {data.get('clients')}", "SUCCESS")
                        elif msg_type == 'transmission_started':
                            self.log(f"Device '{data.get('device')}' started talking", "INFO")
                        elif msg_type == 'transmission_ended':
                            self.log(f"Device '{data.get('device')}' stopped talking", "INFO")
                        else:
                            self.log(f"Received message: {data}", "INFO")
                    except json.JSONDecodeError:
                        self.log(f"Received non-JSON text: {message}", "WARNING")

        except websockets.exceptions.ConnectionClosed:
            self.log("Connection closed by server", "WARNING")
        except Exception as e:
            self.log(f"Error receiving messages: {e}", "ERROR")

    async def simulate_transmission(self, duration_ms=2000):
        """Simulate a complete transmission cycle"""
        self.log("=== Simulating PTT transmission ===", "INFO")
        await self.start_transmission()
        await self.send_audio(duration_ms)
        await self.end_transmission()
        self.log("=== Transmission complete ===", "INFO")


async def run_interactive_client(device_name, server_url):
    """Run an interactive client that accepts commands"""
    client = SimulatedWalkieTalkie(device_name, server_url)

    if not await client.connect():
        return

    await client.register()

    # Start receiving messages in background
    receive_task = asyncio.create_task(client.receive_messages())

    print("\n" + "="*60)
    print(f"Interactive Walkie-Talkie: {device_name}")
    print("="*60)
    print("Commands:")
    print("  t / talk [ms]  - Transmit audio (default 2000ms)")
    print("  s / status     - Show status")
    print("  q / quit       - Quit")
    print("="*60 + "\n")

    try:
        while True:
            try:
                # Get user input (in async context)
                command = await asyncio.get_event_loop().run_in_executor(
                    None, input, f"\n[{device_name}] > "
                )

                command = command.strip().lower()
                parts = command.split()

                if not parts:
                    continue

                cmd = parts[0]

                if cmd in ['q', 'quit', 'exit']:
                    client.log("Quitting...", "INFO")
                    break
                elif cmd in ['t', 'talk']:
                    duration = int(parts[1]) if len(parts) > 1 else 2000
                    await client.simulate_transmission(duration)
                elif cmd in ['s', 'status']:
                    client.log(f"Status: {'Transmitting' if client.is_transmitting else 'Idle'}", "INFO")
                    client.log(f"Audio chunks received: {client.received_audio_count}", "INFO")
                else:
                    print(f"Unknown command: {cmd}")

            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                client.log(f"Command error: {e}", "ERROR")

    finally:
        receive_task.cancel()
        if client.websocket:
            await client.websocket.close()
        client.log("Disconnected", "INFO")


async def run_automated_test(device_name, server_url, test_sequence):
    """Run automated test sequence"""
    client = SimulatedWalkieTalkie(device_name, server_url)

    if not await client.connect():
        return

    await client.register()

    # Start receiving messages in background
    receive_task = asyncio.create_task(client.receive_messages())

    try:
        for action in test_sequence:
            action_type = action['type']

            if action_type == 'wait':
                duration = action.get('duration', 1)
                client.log(f"Waiting {duration}s...", "INFO")
                await asyncio.sleep(duration)
            elif action_type == 'transmit':
                duration_ms = action.get('duration_ms', 2000)
                await client.simulate_transmission(duration_ms)
            elif action_type == 'sleep':
                duration = action.get('duration', 1)
                await asyncio.sleep(duration)

    finally:
        receive_task.cancel()
        if client.websocket:
            await client.websocket.close()
        client.log("Test complete", "SUCCESS")


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Interactive mode: python test_client.py <device_name> [server_url]")
        print("  Example: python test_client.py Alice ws://localhost:8080/walkie")
        print()
        print("Default server: ws://localhost:8080/walkie")
        sys.exit(1)

    device_name = sys.argv[1]
    server_url = sys.argv[2] if len(sys.argv) > 2 else "ws://localhost:8080/walkie"

    await run_interactive_client(device_name, server_url)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nShutdown requested...exiting")
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
