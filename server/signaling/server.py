#!/usr/bin/env python3
"""WiFi Walkie-Talkie Signaling Bridge Server - Peer-to-Peer WebRTC"""
import asyncio, glob, json, logging, os, time, wave
from datetime import datetime
from typing import Dict, Optional, Set, List
from collections import deque
import websockets
from websockets.server import serve

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PORT = 8080
HOST = '0.0.0.0'
TURN_SERVER = os.environ.get('TURN_SERVER', 'wifi-talkie.spottenn.com:3478')
TURN_USER = os.environ.get('TURN_USER', 'walkie')
TURN_PASSWORD = os.environ.get('TURN_PASSWORD', 'talkie')
RECORDING_ENABLED = True
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), 'recordings')
SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2
CHANNELS = 1

class DeviceConnection:
    def __init__(self, websocket, device_name: str):
        self.websocket = websocket
        self.device_name = device_name
        self.is_transmitting = False
        self.connected_at = datetime.now()

class TransmissionRecording:
    def __init__(self, device_name: str):
        self.device_name = device_name
        self.audio_data: List[bytes] = []
        self.start_time = datetime.now()
        self.filename: Optional[str] = None

class SignalingBridge:
    def __init__(self):
        self.devices: Dict = {}
        self.current_recording: Optional[TransmissionRecording] = None
        self.transmitting_devices: Set[str] = set()

    def ensure_recordings_directory(self):
        if RECORDING_ENABLED and not os.path.exists(RECORDINGS_DIR):
            os.makedirs(RECORDINGS_DIR)

    def start_recording(self, device_name: str):
        if not RECORDING_ENABLED: return
        self.ensure_recordings_directory()
        self.current_recording = TransmissionRecording(device_name)
        timestamp = self.current_recording.start_time.strftime('%Y%m%d_%H%M%S')
        self.current_recording.filename = os.path.join(RECORDINGS_DIR, f'transmission_{timestamp}_{device_name}.wav')

    def add_audio_packet(self, audio_data: bytes):
        if self.current_recording: self.current_recording.audio_data.append(audio_data)

    def save_recording(self):
        if not self.current_recording or not self.current_recording.audio_data:
            self.current_recording = None
            return
        combined = b''.join(self.current_recording.audio_data)
        try:
            with wave.open(self.current_recording.filename, 'wb') as f:
                f.setnchannels(CHANNELS); f.setsampwidth(SAMPLE_WIDTH)
                f.setframerate(SAMPLE_RATE); f.writeframes(combined)
            logger.info(f'Saved: {self.current_recording.filename}')
        except Exception as e: logger.error(f'Save error: {e}')
        finally: self.current_recording = None

    async def broadcast_message(self, message: dict, exclude=None):
        msg_str = json.dumps(message)
        for ws, dev in list(self.devices.items()):
            if ws != exclude:
                try: await ws.send(msg_str)
                except: pass

    async def handle_register(self, websocket, data: dict):
        device_name = data.get('device', f'device_{id(websocket)}')
        self.devices[websocket] = DeviceConnection(websocket, device_name)
        logger.info(f'Device registered: {device_name} (total: {len(self.devices)})')
        all_devices = [d.device_name for d in self.devices.values()]
        await websocket.send(json.dumps({
            'type': 'registered', 'device': device_name, 'devices': all_devices,
            'turn': {'server': TURN_SERVER, 'user': TURN_USER, 'password': TURN_PASSWORD}
        }))
        await self.broadcast_message({'type': 'device_joined', 'device': device_name, 'clients': len(self.devices)}, exclude=websocket)

    async def handle_ptt_start(self, websocket, data: dict):
        device = self.devices.get(websocket)
        if not device: return
        device.is_transmitting = True
        self.transmitting_devices.add(device.device_name)
        logger.info(f'PTT START: {device.device_name}')
        if len(self.transmitting_devices) == 1: self.start_recording(device.device_name)
        await self.broadcast_message({'type': 'ptt_start', 'device': device.device_name})

    async def handle_ptt_end(self, websocket, data: dict):
        device = self.devices.get(websocket)
        if not device: return
        device.is_transmitting = False
        self.transmitting_devices.discard(device.device_name)
        logger.info(f'PTT END: {device.device_name}')
        if len(self.transmitting_devices) == 0: self.save_recording()
        await self.broadcast_message({'type': 'ptt_end', 'device': device.device_name})

    async def handle_offer(self, websocket, data: dict):
        device = self.devices.get(websocket)
        if not device: return
        logger.info(f'SDP Offer from {device.device_name}, forwarding')
        await self.broadcast_message({'type': 'offer', 'device': device.device_name, 'sdp': data.get('sdp', '')}, exclude=websocket)

    async def handle_answer(self, websocket, data: dict):
        device = self.devices.get(websocket)
        if not device: return
        logger.info(f'SDP Answer from {device.device_name}')
        await self.broadcast_message({'type': 'answer', 'device': device.device_name, 'sdp': data.get('sdp', '')}, exclude=websocket)

    async def handle_candidate(self, websocket, data: dict):
        device = self.devices.get(websocket)
        if not device: return
        await self.broadcast_message({'type': 'candidate', 'device': device.device_name, 'candidate': data.get('candidate', '')}, exclude=websocket)

    async def handle_audio_data(self, websocket, audio_bytes: bytes):
        device = self.devices.get(websocket)
        if not device or not device.is_transmitting: return
        self.add_audio_packet(audio_bytes)
        for ws, dev in list(self.devices.items()):
            if ws != websocket and not dev.is_transmitting:
                try: await ws.send(audio_bytes)
                except: pass

    async def handle_message(self, websocket, message):
        if isinstance(message, bytes):
            await self.handle_audio_data(websocket, message)
            return
        try:
            data = json.loads(message)
            msg_type = data.get('type', '')
            device = self.devices.get(websocket)
            logger.info(f"Received: {msg_type} from {device.device_name if device else 'unknown'}")
            handlers = {'register': self.handle_register, 'ptt_start': self.handle_ptt_start, 'ptt_end': self.handle_ptt_end,
                       'offer': self.handle_offer, 'answer': self.handle_answer, 'candidate': self.handle_candidate}
            handler = handlers.get(msg_type)
            if handler: await handler(websocket, data)
            else: logger.warning(f'Unknown: {msg_type}')
        except json.JSONDecodeError as e: logger.error(f'Invalid JSON: {e}')

    async def handle_connection(self, websocket):
        logger.info(f'New connection from {websocket.remote_address}')
        try:
            async for message in websocket: await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed: pass
        except Exception as e: logger.error(f'Error: {e}')
        finally:
            device = self.devices.pop(websocket, None)
            if device:
                self.transmitting_devices.discard(device.device_name)
                logger.info(f'Device disconnected: {device.device_name}')
                await self.broadcast_message({'type': 'device_left', 'device': device.device_name, 'clients': len(self.devices)})
                if len(self.transmitting_devices) == 0 and self.current_recording: self.save_recording()

    async def run(self):
        logger.info('WiFi Walkie-Talkie Signaling Bridge')
        logger.info(f'Listening on {HOST}:{PORT}, TURN: {TURN_SERVER}')
        async with serve(self.handle_connection, HOST, PORT): await asyncio.Future()

async def main():
    bridge = SignalingBridge()
    await bridge.run()

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: logger.info('Server stopped')
