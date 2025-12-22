# Testing Guide

This guide explains how to test the WiFi walkie-talkie system without physical hardware.

## Overview

We provide Python scripts that simulate M5Stack Atom Echo devices, allowing you to test the complete system on your computer.

## Quick Start

### 1. Start the Server

```bash
cd server
pip install websockets
python server.py
```

You should see:
```
========================================
WiFi Walkie-Talkie Server
========================================
Starting server on 0.0.0.0:8080
WebSocket endpoint: ws://0.0.0.0:8080/walkie
========================================
```

### 2. Run Automated Test

In a new terminal:

```bash
python test_bidirectional.py
```

This will:
- Create two simulated devices (Alice and Bob)
- Connect both to the server
- Test Alice → Bob communication
- Test Bob → Alice communication
- Test rapid back-and-forth communication
- Display a test summary

## Interactive Testing

### Single Device Test

Run an interactive client that you can control manually:

```bash
python test_client.py Alice
```

Commands:
- `t` or `talk` - Transmit audio for 2 seconds
- `talk 5000` - Transmit audio for 5 seconds (custom duration)
- `s` or `status` - Show device status
- `q` or `quit` - Exit

### Multiple Devices

Open multiple terminals and run different devices:

```bash
# Terminal 1
python test_client.py Alice

# Terminal 2
python test_client.py Bob

# Terminal 3
python test_client.py Charlie
```

Now you can type `t` in one terminal to transmit, and watch the others receive!

## Test Scripts

### test_client.py

**Purpose**: Simulates a single M5Stack Atom Echo device

**Features**:
- WebSocket connection to server
- Device registration
- Push-to-talk simulation
- Audio transmission (simulated binary data)
- Audio reception logging
- Colored console output
- Interactive command interface

**Usage**:
```bash
python test_client.py <device_name> [server_url]

# Examples
python test_client.py Alice
python test_client.py Bob ws://192.168.1.100:8080/walkie
```

### test_bidirectional.py

**Purpose**: Automated bidirectional communication test

**Features**:
- Creates two simulated devices automatically
- Tests both directions of communication
- Verifies audio chunk delivery
- Stress tests with rapid back-and-forth
- Detailed test reporting
- Exit code for CI/CD integration

**Usage**:
```bash
python test_bidirectional.py [server_url]

# Examples
python test_bidirectional.py
python test_bidirectional.py ws://192.168.1.100:8080/walkie
```

**Exit Codes**:
- `0`: All tests passed
- `1`: One or more tests failed

## Understanding the Output

### Color Coding

The test clients use colored output:

- **Blue** - Informational messages
- **Green** - Success messages
- **Yellow** - Warnings
- **Red** - Errors
- **Magenta** - Audio data transmission/reception

### Sample Output

```
[03:58:47.008] [Alice] INFO: === Simulating PTT transmission ===
[03:58:47.008] [Alice] SUCCESS: Started transmission (PTT pressed)
[03:58:47.008] [Alice] AUDIO: Sent audio chunk: 512 bytes
[03:58:47.011] [Bob] AUDIO: Received audio data: 512 bytes (total chunks: 1)
[03:58:47.042] [Alice] AUDIO: Sent audio chunk: 512 bytes
[03:58:47.043] [Bob] AUDIO: Received audio data: 512 bytes (total chunks: 2)
...
[03:58:49.113] [Alice] SUCCESS: Ended transmission (PTT released)
```

### Server Output

The server logs show relay activity:

```
2025-12-22 03:58:47,009 - INFO - Alice started transmitting
2025-12-22 03:58:47,010 - INFO - Audio broadcasted to 1/1 clients
2025-12-22 03:58:47,043 - INFO - Audio broadcasted to 1/1 clients
...
2025-12-22 03:58:49,113 - INFO - Alice stopped transmitting
```

## What Gets Tested

### Connection Testing
- WebSocket connection establishment
- Device registration
- Multiple simultaneous connections
- Connection stability

### Audio Relay Testing
- Binary data transmission
- Server-side broadcast to other clients
- Packet ordering
- No echo back to sender

### Protocol Testing
- JSON control messages
- Binary audio data frames
- Start/stop transmission signals
- Device naming and identification

## Simulated Audio Data

The test clients generate **random binary data** to simulate audio:

- **Sample Rate**: 16,000 Hz
- **Bit Depth**: 16-bit (2 bytes per sample)
- **Chunk Size**: 512 bytes = 256 samples
- **Chunk Duration**: ~16ms at 16kHz
- **1 second transmission**: ~63 chunks

This matches the actual M5Stack Atom Echo configuration.

## Troubleshooting

### Server won't start

**Error**: `ModuleNotFoundError: No module named 'websockets'`

**Solution**:
```bash
pip install websockets
```

### Can't connect to server

**Error**: `Connection failed: [Errno 111] Connection refused`

**Solution**:
1. Ensure server is running
2. Check server address (default: `ws://localhost:8080/walkie`)
3. Check firewall settings

### No audio received

**Possible causes**:
1. Only one device connected (need at least 2)
2. Device not transmitting
3. Server not running
4. Wrong server URL

**Debug**:
```bash
# Check server logs for "Audio broadcasted to X clients"
# Should show X >= 1 when another device is connected
```

## CI/CD Integration

Run automated tests in your CI pipeline:

```bash
# Start server in background
python server/server.py &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Run tests
python test_bidirectional.py
TEST_RESULT=$?

# Cleanup
kill $SERVER_PID

# Exit with test result
exit $TEST_RESULT
```

## Performance Testing

### Load Testing

Test with many simultaneous devices:

```bash
# Create script to spawn multiple clients
for i in {1..10}; do
  python test_client.py "Device$i" &
done

# Wait for all to connect, then transmit from one device
# Server should broadcast to all 9 other devices
```

### Latency Testing

Measure round-trip time by adding timestamps to audio chunks (requires modifying test scripts).

### Bandwidth Testing

Monitor network usage during transmission:

```bash
# Linux
iftop -i lo  # Monitor localhost interface

# Expected bandwidth per transmitting device:
# 512 bytes/chunk × 31.25 chunks/sec ≈ 16 KB/s
# At 16kHz, 16-bit: 32 KB/s raw audio
```

## Next Steps

After successful simulated testing:

1. **Build firmware**: `pio run` in main directory
2. **Upload to M5Stack Atom Echo**: `pio run --target upload`
3. **Test with real hardware**: Press button, speak, listen on other device
4. **Deploy server**: See `server/README.md` for deployment options

## See Also

- `TEST_RESULTS.md` - Detailed test results from latest run
- `README.md` - Project overview and setup
- `server/README.md` - Server deployment guide
- `QUICKSTART.md` - Quick start guide

---

**Happy Testing! 🧪**
