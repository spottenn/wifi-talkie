# WiFi Walkie-Talkie Project - Handoff Packet

## Current Status: READY FOR USE (December 25, 2025)

All major audio quality issues have been fixed and tested. All 3 walkie-talkies are flashed and ready for Christmas!

### What Works
- All devices connect to WiFi and WebSocket server
- LED indicators work correctly (red/green/blue/yellow)
- Button press triggers transmission (blue LED)
- Receiving device shows yellow LED
- Audio is transmitted, received, and plays at good volume
- Server correctly relays audio to all clients
- Auto-cleanup after transmission (no buzzing)

## Issues Fixed This Session

### 1. Buzzing After Transmission Stops - FIXED
**Root cause**: DMA buffers contained stale audio data that looped as buzzing
**Fix**:
- Added `flushSpeakerWithSilence()` function that writes zeros to I2S before mode switch
- Added 300ms timeout to auto-switch from speaker to mic mode after audio stops
**Test result**: Receiver logs show `[AUTO] Speaker timeout - switching to mic mode`

### 2. Audio Too Soft - FIXED
**Root cause**: Raw PDM microphone data has very low amplitude
**Fix**: Added 8x gain amplification in `transmitAudio()` with clipping protection
**Test result**: Average amplitude increased from ~100 to ~12,000

### 3. Audio Freezing/Glitches - FIXED
**Root cause**: Tiny DMA buffers (2 x 128 = 256 samples = 16ms)
**Fix**: Increased to 8 x 256 = 2048 samples = 128ms buffer
**Test result**: Consistent ~31ms inter-packet timing with smooth playback

## Audio Quality (Verified)

- Average amplitude: ~12,000 (target was >2,000)
- No clipping even with loud input
- Smooth 31ms packet timing
- Auto-switch to mic mode after 300ms silence

## Hardware Reality: M5Stack Atom Echo

**Critical Discovery**: The Atom Echo shares GPIO 33 between microphone and speaker. They CANNOT operate simultaneously on separate I2S ports.

**Solution Implemented**: Dynamic I2S mode switching with proper cleanup
- When receiving audio: switch I2S_NUM_0 to speaker mode
- When transmitting: switch I2S_NUM_0 to mic mode
- After receiving: auto-switch back to mic mode after 300ms timeout with silence flush

### Pin Configuration
```
Microphone (PDM):
  - WS/CLK: GPIO 33
  - DATA: GPIO 23

Speaker (I2S):
  - BCK: GPIO 19
  - WS/LRCK: GPIO 33  <-- SHARED!
  - DATA: GPIO 22
```

## Environment

### User's Machine
- **OS**: Windows 11
- **Python**: C:\Users\spott\AppData\Local\Programs\Python\Python312
- **PlatformIO**: Installed via pip
- **Project Path**: C:\Users\spott\claude-code\wifi-talkie

### Running the Server
```powershell
cd C:\Users\spott\claude-code\wifi-talkie\server
C:\Users\spott\AppData\Local\Programs\Python\Python312\python.exe server.py
```
Server runs on 0.0.0.0:8080

### Flashing Devices
```powershell
cd C:\Users\spott\claude-code\wifi-talkie

# Edit .env to set DEVICE_NAME, then:
# Note: set PYTHONIOENCODING=utf-8 if configure.py fails with unicode errors
set PYTHONIOENCODING=utf-8 && C:\Users\spott\AppData\Local\Programs\Python\Python312\python.exe configure.py
C:\Users\spott\AppData\Local\Programs\Python\Python312\Scripts\pio.exe run --target upload --upload-port COM9
```

## Current Configuration

### .env File
```
WIFI_SSID_1=NETGEAR52
WIFI_PASSWORD_1=youshallnotpass

WIFI_SSID_2=FBISurveillanceVan
WIFI_PASSWORD_2=SkiGoose9293

WIFI_SSID_3=Network Not Found
WIFI_PASSWORD_3=Tlbrett123

WEBSOCKET_SERVER=ws://192.168.0.178:8080
DEVICE_NAME=<set per device>
```

### Devices Configured
| Name | COM Port | MAC Address |
|------|----------|-------------|
| Walkie-Dad | - | 90:15:06:fd:5b:c4 |
| Larsens | - | f4:65:0b:08:4b:88 |
| Walkie-3 | - | f4:65:0b:08:4d:f4 |

### Server IP
- Computer IP: 192.168.0.178
- Firewall rule added for port 8080

## Debug Commands (Serial)

```powershell
C:\Users\spott\AppData\Local\Programs\Python\Python312\Scripts\pio.exe device monitor --port COM9 --baud 115200
```
Then type: `T` (transmit 3s), `S` (stop), `?` (status)

## Key Files Modified

### src/main.cpp
Major changes:
- Added `flushSpeakerWithSilence()` - prevents buzzing
- Added 300ms speaker timeout for auto-switch to mic mode
- Added 8x audio gain with clipping protection
- Increased DMA buffers from 2x128 to 8x256
- Added debug serial commands: T, S, ?
- `lastAudioReceived` timestamp tracking

### server/server.py
- Added audio recording to server/recordings/*.wav
- Added quality analysis: amplitude, duration, packet timing
- Logs detailed analysis after each transmission

### include/config.h
- AUDIO_BUFFER_SIZE = 512
- SAMPLE_RATE = 16000

## Project Philosophy

- **Simple**: Press button = talk
- **Reliable**: Auto-reconnect, multi-network support
- **Kid-friendly**: Clear LED status indicators
- **No auth needed**: Trusted home network

## Git Status

- Branch: main
- Repository: spottenn/wifi-talkie
- All changes committed and pushed

---

## For Continuing Claude Instance

**Current State**: All audio issues fixed. All 3 devices flashed and ready for production use.

**Devices**:
- Walkie-Dad (MAC: 90:15:06:fd:5b:c4)
- Larsens (MAC: f4:65:0b:08:4b:88)
- Walkie-3 (MAC: f4:65:0b:08:4d:f4)

**What was fixed**:
1. Buzzing: Added silence flush + auto-timeout switch to mic mode
2. Soft audio: Added 8x gain amplification
3. Glitches: Increased DMA buffers 8x

**Hardware Constraint**: GPIO 33 is shared between mic and speaker. You MUST switch I2S modes - cannot use separate I2S ports.

**Quick Commands**:
```powershell
# Full path to Python with platformio (use cmd //c wrapper if in bash)
C:\Users\spott\AppData\Local\Programs\Python\Python312\Scripts\pio.exe run --target upload --upload-port COM9

# Run server
C:\Users\spott\AppData\Local\Programs\Python\Python312\python.exe server\server.py

# Monitor device
C:\Users\spott\AppData\Local\Programs\Python\Python312\Scripts\pio.exe device monitor --port COM9 --baud 115200

# Configure before flashing (needs UTF-8 on Windows)
set PYTHONIOENCODING=utf-8 && C:\Users\spott\AppData\Local\Programs\Python\Python312\python.exe configure.py
```
