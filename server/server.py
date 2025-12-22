#!/usr/bin/env python3
"""
WiFi Walkie-Talkie WebSocket Server (Python version)

This server relays audio data between all connected walkie-talkie devices.
When one device transmits, all other devices receive the audio.

Requirements:
    pip install websockets asyncio
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set
import websockets
from websockets.server import serve

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Server configuration
PORT = 8080
HOST = '0.0.0.0'

# Store connected clients
clients: Set[websockets.WebSocketServerProtocol] = set()
transmitting_client = None


async def register_client(websocket):
    """Register a new client connection."""
    clients.add(websocket)
    logger.info(f"New client connected from {websocket.remote_address}")
    logger.info(f"Total clients: {len(clients)}")

    # Send welcome message
    await websocket.send(json.dumps({
        'type': 'welcome',
        'message': 'Connected to WiFi Walkie-Talkie server',
        'clients': len(clients)
    }))


async def unregister_client(websocket):
    """Unregister a client connection."""
    global transmitting_client

    clients.discard(websocket)
    if transmitting_client == websocket:
        transmitting_client = None

    logger.info(f"Client disconnected from {websocket.remote_address}")
    logger.info(f"Total clients: {len(clients)}")


async def broadcast_audio(data: bytes, sender):
    """Broadcast audio data to all clients except sender."""
    if not clients:
        return

    sent_count = 0
    # Send to all clients except the sender
    tasks = []
    for client in clients:
        if client != sender:
            tasks.append(send_audio(client, data))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    sent_count = sum(1 for r in results if r is True)

    logger.info(f"Audio broadcasted to {sent_count}/{len(clients)-1} clients")


async def send_audio(client, data: bytes):
    """Send audio data to a specific client."""
    try:
        await client.send(data)
        return True
    except Exception as e:
        logger.error(f"Error sending audio to client: {e}")
        return False


async def broadcast_message(message: dict, exclude=None):
    """Broadcast a JSON message to all clients except excluded one."""
    message_str = json.dumps(message)
    tasks = []

    for client in clients:
        if client != exclude:
            tasks.append(send_message(client, message_str))

    await asyncio.gather(*tasks, return_exceptions=True)


async def send_message(client, message: str):
    """Send a text message to a specific client."""
    try:
        await client.send(message)
    except Exception as e:
        logger.error(f"Error sending message to client: {e}")


async def handle_client(websocket):
    """Handle a client connection."""
    global transmitting_client

    # Register client
    await register_client(websocket)

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # Binary data = audio
                logger.info(f"Received audio data: {len(message)} bytes from {websocket.remote_address}")
                await broadcast_audio(message, websocket)
            else:
                # Text data = control messages
                try:
                    data = json.loads(message)
                    logger.info(f"Received message from {websocket.remote_address}: {data}")

                    msg_type = data.get('type')

                    if msg_type == 'register':
                        device_name = data.get('device', 'unknown')
                        websocket.device_name = device_name
                        logger.info(f"Client registered as: {device_name}")

                        # Send confirmation
                        await websocket.send(json.dumps({
                            'type': 'registered',
                            'clients': len(clients)
                        }))

                    elif msg_type == 'start_transmission':
                        transmitting_client = websocket
                        device_name = getattr(websocket, 'device_name', 'unknown')
                        logger.info(f"{device_name} started transmitting")

                        # Notify other clients
                        await broadcast_message({
                            'type': 'transmission_started',
                            'device': device_name
                        }, exclude=websocket)

                    elif msg_type == 'end_transmission':
                        if transmitting_client == websocket:
                            transmitting_client = None
                        device_name = getattr(websocket, 'device_name', 'unknown')
                        logger.info(f"{device_name} stopped transmitting")

                        # Notify other clients
                        await broadcast_message({
                            'type': 'transmission_ended',
                            'device': device_name
                        }, exclude=websocket)

                    else:
                        logger.warning(f"Unknown message type: {msg_type}")

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON: {e}")

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed normally for {websocket.remote_address}")
    except Exception as e:
        logger.error(f"Error handling client {websocket.remote_address}: {e}")
    finally:
        await unregister_client(websocket)


async def main():
    """Start the WebSocket server."""
    logger.info("=" * 40)
    logger.info("WiFi Walkie-Talkie Server")
    logger.info("=" * 40)
    logger.info(f"Starting server on {HOST}:{PORT}")
    logger.info(f"WebSocket endpoint: ws://{HOST}:{PORT}/walkie")
    logger.info("=" * 40)

    async with serve(handle_client, HOST, PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
