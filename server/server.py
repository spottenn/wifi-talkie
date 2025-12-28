#!/usr/bin/env python3
"""
WiFi Walkie-Talkie WebSocket Server (Python version)

This server relays audio data between all connected walkie-talkie devices.
Supports multiple simultaneous transmitters by mixing audio streams.

Requirements:
    pip install websockets asyncio
"""

import asyncio
import json
import logging
import os
import struct
import wave
from datetime import datetime
from typing import Set, Optional, List, Dict
from collections import deque
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

# Recording configuration
RECORDING_ENABLED = True
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), 'recordings')

# Audio format constants
SAMPLE_RATE = 16000  # 16 kHz
SAMPLE_WIDTH = 2     # 16-bit = 2 bytes
CHANNELS = 1         # Mono
SAMPLES_PER_PACKET = 512  # Expected samples per packet

# Mixer configuration
MIXER_INTERVAL_MS = 30  # Mix and broadcast every 30ms

# Store connected clients
clients: Set[websockets.WebSocketServerProtocol] = set()
transmitting_clients: Set[websockets.WebSocketServerProtocol] = set()

# Audio buffers for mixing (one queue per transmitting client)
audio_queues: Dict[websockets.WebSocketServerProtocol, deque] = {}

# Recording state for current transmission
class TransmissionRecording:
    def __init__(self, device_name: str):
        self.device_name = device_name
        self.audio_data: List[bytes] = []
        self.packet_times: List[float] = []
        self.start_time = datetime.now()
        self.filename: Optional[str] = None

current_recording: Optional[TransmissionRecording] = None


def ensure_recordings_directory():
    """Create recordings directory if it doesn't exist."""
    if RECORDING_ENABLED and not os.path.exists(RECORDINGS_DIR):
        os.makedirs(RECORDINGS_DIR)
        logger.info(f"Created recordings directory: {RECORDINGS_DIR}")


def start_recording(device_name: str):
    """Start recording a new transmission."""
    global current_recording

    if not RECORDING_ENABLED:
        return

    ensure_recordings_directory()

    # Create new recording with timestamp
    current_recording = TransmissionRecording(device_name)
    timestamp = current_recording.start_time.strftime('%Y%m%d_%H%M%S')
    current_recording.filename = os.path.join(
        RECORDINGS_DIR,
        f'transmission_{timestamp}.wav'
    )

    logger.info(f"Started recording: {current_recording.filename}")


def add_audio_packet(audio_data: bytes):
    """Add an audio packet to the current recording."""
    global current_recording

    if not RECORDING_ENABLED or current_recording is None:
        return

    current_recording.audio_data.append(audio_data)
    current_recording.packet_times.append(datetime.now().timestamp())


def analyze_audio_quality(audio_data: bytes, packet_times: List[float]):
    """
    Analyze audio quality and return statistics.

    Args:
        audio_data: Combined raw PCM audio data
        packet_times: List of timestamps when packets were received

    Returns:
        dict with analysis results
    """
    # Calculate duration based on sample count
    num_samples = len(audio_data) // SAMPLE_WIDTH
    duration_sec = num_samples / SAMPLE_RATE

    # Calculate average amplitude
    # Unpack 16-bit signed integers
    samples = struct.unpack(f'<{num_samples}h', audio_data)
    abs_samples = [abs(s) for s in samples]
    avg_amplitude = sum(abs_samples) / len(abs_samples) if abs_samples else 0

    # Check for silence at end (last 100ms)
    samples_in_100ms = int(SAMPLE_RATE * 0.1)  # 1600 samples for 100ms at 16kHz
    if len(abs_samples) >= samples_in_100ms:
        last_100ms_samples = abs_samples[-samples_in_100ms:]
        avg_end_amplitude = sum(last_100ms_samples) / len(last_100ms_samples)
        has_silence_at_end = avg_end_amplitude < 100
    else:
        has_silence_at_end = False
        avg_end_amplitude = avg_amplitude

    # Calculate packet timing statistics
    packet_stats = {}
    if len(packet_times) > 1:
        inter_packet_delays = [
            (packet_times[i] - packet_times[i-1]) * 1000  # Convert to ms
            for i in range(1, len(packet_times))
        ]
        packet_stats = {
            'packet_count': len(packet_times),
            'avg_inter_packet_delay_ms': sum(inter_packet_delays) / len(inter_packet_delays),
            'min_inter_packet_delay_ms': min(inter_packet_delays),
            'max_inter_packet_delay_ms': max(inter_packet_delays)
        }
    else:
        packet_stats = {
            'packet_count': len(packet_times),
            'avg_inter_packet_delay_ms': 0,
            'min_inter_packet_delay_ms': 0,
            'max_inter_packet_delay_ms': 0
        }

    return {
        'duration_sec': duration_sec,
        'avg_amplitude': avg_amplitude,
        'avg_end_amplitude': avg_end_amplitude,
        'has_silence_at_end': has_silence_at_end,
        **packet_stats
    }


def save_recording_and_analyze():
    """Save the current recording to WAV file and analyze it."""
    global current_recording

    if not RECORDING_ENABLED or current_recording is None:
        return

    if not current_recording.audio_data:
        logger.warning("No audio data to save")
        current_recording = None
        return

    # Combine all audio packets
    combined_audio = b''.join(current_recording.audio_data)

    # Save to WAV file
    try:
        with wave.open(current_recording.filename, 'wb') as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(SAMPLE_WIDTH)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(combined_audio)

        logger.info(f"Saved recording: {current_recording.filename} ({len(combined_audio)} bytes)")

        # Analyze audio quality
        analysis = analyze_audio_quality(combined_audio, current_recording.packet_times)

        # Log analysis results
        logger.info("=" * 60)
        logger.info(f"Audio Quality Analysis for {current_recording.device_name}")
        logger.info("=" * 60)
        logger.info(f"File: {os.path.basename(current_recording.filename)}")
        logger.info(f"Duration: {analysis['duration_sec']:.2f} seconds")
        logger.info(f"Average Amplitude: {analysis['avg_amplitude']:.2f}")
        logger.info(f"End Amplitude (last 100ms): {analysis['avg_end_amplitude']:.2f}")
        logger.info(f"Silence at End: {'Yes' if analysis['has_silence_at_end'] else 'No'}")
        logger.info(f"Packet Count: {analysis['packet_count']}")
        if analysis['packet_count'] > 1:
            logger.info(f"Avg Inter-Packet Delay: {analysis['avg_inter_packet_delay_ms']:.2f} ms")
            logger.info(f"Min Inter-Packet Delay: {analysis['min_inter_packet_delay_ms']:.2f} ms")
            logger.info(f"Max Inter-Packet Delay: {analysis['max_inter_packet_delay_ms']:.2f} ms")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error saving recording: {e}")
    finally:
        current_recording = None


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
    clients.discard(websocket)
    transmitting_clients.discard(websocket)
    if websocket in audio_queues:
        del audio_queues[websocket]

    logger.info(f"Client disconnected from {websocket.remote_address}")
    logger.info(f"Total clients: {len(clients)}")


def mix_audio_packets(packets: List[bytes]) -> bytes:
    """Mix multiple audio packets together by adding samples with clipping."""
    if not packets:
        return b''
    if len(packets) == 1:
        return packets[0]

    # Find the longest packet
    max_len = max(len(p) for p in packets)
    num_samples = max_len // SAMPLE_WIDTH

    # Mix all packets
    mixed = [0] * num_samples
    for packet in packets:
        samples = struct.unpack(f'<{len(packet)//SAMPLE_WIDTH}h', packet)
        for i, sample in enumerate(samples):
            mixed[i] += sample

    # Clip to 16-bit range
    clipped = []
    for sample in mixed:
        if sample > 32767:
            sample = 32767
        elif sample < -32768:
            sample = -32768
        clipped.append(sample)

    return struct.pack(f'<{len(clipped)}h', *clipped)


async def broadcast_audio(data: bytes, sender):
    """Mix and broadcast audio immediately when received."""
    # Collect this packet plus any waiting packets from other transmitters
    packets = [data]
    senders = {sender}

    # Check if other transmitters have packets waiting
    for client in list(transmitting_clients):
        if client != sender and client in audio_queues and audio_queues[client]:
            packets.append(audio_queues[client].popleft())
            senders.add(client)

    # If there are other transmitters but no packets ready, queue this one briefly
    other_transmitters = transmitting_clients - {sender}
    if other_transmitters and len(packets) == 1:
        # Queue this packet for the other transmitter to pick up
        if sender not in audio_queues:
            audio_queues[sender] = deque(maxlen=3)  # Small buffer
        audio_queues[sender].append(data)
        return  # Don't send yet, wait for other transmitter's packet

    # Mix if we have multiple packets
    mixed = mix_audio_packets(packets)

    # Record the mixed audio
    add_audio_packet(mixed)

    # Broadcast to all clients NOT currently transmitting
    tasks = []
    for client in clients:
        if client not in transmitting_clients:
            tasks.append(send_audio(client, mixed))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        sent_count = sum(1 for r in results if r is True)
        if len(senders) > 1:
            logger.info(f"Mixed {len(senders)} streams, sent to {sent_count} clients")


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
    # Register client
    await register_client(websocket)

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # Binary data = audio - queue for mixing
                if websocket in transmitting_clients:
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
                        transmitting_clients.add(websocket)
                        audio_queues[websocket] = deque(maxlen=10)
                        device_name = getattr(websocket, 'device_name', 'unknown')
                        logger.info(f"{device_name} started transmitting ({len(transmitting_clients)} active)")

                        # Start recording if first transmitter
                        if len(transmitting_clients) == 1:
                            start_recording(device_name)

                        # Notify other clients
                        await broadcast_message({
                            'type': 'transmission_started',
                            'device': device_name
                        }, exclude=websocket)

                    elif msg_type == 'end_transmission':
                        transmitting_clients.discard(websocket)
                        if websocket in audio_queues:
                            del audio_queues[websocket]
                        device_name = getattr(websocket, 'device_name', 'unknown')
                        logger.info(f"{device_name} stopped transmitting ({len(transmitting_clients)} active)")

                        # Save recording if no more transmitters
                        if len(transmitting_clients) == 0:
                            save_recording_and_analyze()

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
        # Clean up on disconnect
        transmitting_clients.discard(websocket)
        if websocket in audio_queues:
            del audio_queues[websocket]
        await unregister_client(websocket)


async def main():
    """Start the WebSocket server."""
    logger.info("=" * 40)
    logger.info("WiFi Walkie-Talkie Server")
    logger.info("=" * 40)
    logger.info(f"Starting server on {HOST}:{PORT}")
    logger.info(f"WebSocket endpoint: ws://{HOST}:{PORT}/walkie")
    logger.info("Audio mixing: immediate (low-latency)")
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
