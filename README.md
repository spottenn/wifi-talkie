# WiFi Walkie-Talkie

Internet-connected walkie-talkies for kids using M5Stack Atom Echo devices.

## Overview

This project implements a simple push-to-talk walkie-talkie system using:
- **Hardware**: M5Stack Atom Echo (ESP32-based with built-in mic, speaker, and button)
- **Connectivity**: WiFi-based real-time communication via WebSocket
- **Architecture**: Client-server model where devices connect to a central relay server

## Features

- ✅ Single-button push-to-talk operation
- ✅ Real-time audio streaming between all connected devices
- ✅ Visual LED feedback (red=disconnected, green=connected, blue=transmitting, yellow=receiving)
- ✅ Automatic WiFi and WebSocket reconnection
- ✅ Hardcoded WiFi credentials for kid-friendly setup
- ✅ Battery-powered operation (USB power banks)

## Hardware Requirements

### M5Stack Atom Echo Specifications

- **Microcontroller**: ESP32-PICO-D4 (dual-core, 240 MHz)
- **Memory**: 4MB Flash
- **Connectivity**: WiFi 802.11 b/g/n (2.4GHz), Bluetooth 4.0
- **Audio**: Built-in microphone (SPM1423) and speaker
- **Input**: Single programmable button
- **Display**: RGB LED (SK6812)
- **Size**: 24 x 24 x 17 mm
- **Power**: 5V via USB-C or Grove connector

### Additional Requirements

- USB-C cable for programming
- Large USB power bank for portable operation
- WiFi network (2.4GHz)

## Software Setup

### 1. Install PlatformIO

PlatformIO is the recommended development environment:

```bash
# Install PlatformIO Core (CLI)
pip install platformio

# Or use VSCode extension
# Install "PlatformIO IDE" from VSCode marketplace
```

### 2. Configure

```bash
cd wifi-talkie

# Copy example config
cp .env.example .env

# Edit .env with your settings
nano .env  # or use any text editor
```

Set in `.env`:
- `WIFI_SSID_1` and `WIFI_PASSWORD_1` - Your WiFi credentials
- `WEBSOCKET_SERVER` - Your computer's IP (e.g., `ws://192.168.0.178:8080`)
- `DEVICE_NAME` - Unique name for each device

### 3. Build and Upload

```bash
# Generate config from .env
python configure.py

# Build and upload to device
pio run --target upload

# Monitor serial output
pio device monitor
```

## Server Setup

You have two options for the relay server:

### Option 1: Node.js Server (Recommended)

```bash
cd server
npm install
npm start

# Server will run on http://0.0.0.0:8080
# WebSocket endpoint: ws://your-ip:8080/walkie
```

### Option 2: Python Server

```bash
cd server
pip install -r requirements.txt
python server.py

# Server will run on http://0.0.0.0:8080
# WebSocket endpoint: ws://your-ip:8080/walkie
```

### Server Deployment Options

1. **Local Network**: Run on your home computer/Raspberry Pi
2. **Cloud Hosting**: Deploy to services like:
   - Heroku (free tier available)
   - Railway.app
   - Render.com
   - DigitalOcean
   - AWS/Google Cloud/Azure

## Development Without Hardware

### Wokwi Simulator

Wokwi provides ESP32 simulation with WiFi support:

1. Visit [wokwi.com](https://wokwi.com/)
2. Create new ESP32 project
3. Copy code from `src/main.cpp`
4. Configure `diagram.json` for hardware layout
5. Run simulation (WiFi connections work!)

**Note**: Audio I2S functionality has limited simulation support. The WebSocket communication and button logic can be fully tested.

### QEMU Emulator

For more advanced debugging:

```bash
# Install ESP-IDF QEMU
# Follow instructions at: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/tools/qemu.html

# Build for QEMU
pio run -e qemu

# Run in QEMU
qemu-system-xtensa -nographic -machine esp32 -drive file=firmware.bin,if=mtd,format=raw
```

## How It Works

### Architecture

```
┌─────────────┐         ┌─────────────┐
│  Device 1   │◄────────┤   Server    ├────────►┌─────────────┐
│  (Atom Echo)│  WebSocket Relay       │         │  Device 2   │
└─────────────┘         └─────────────┘         │  (Atom Echo)│
                                                 └─────────────┘
                                ▲
                                │
                        ┌───────┴────────┐
                        │    Device 3    │
                        │   (Atom Echo)  │
                        └────────────────┘
```

### Communication Flow

1. **Startup**: Each device connects to WiFi, then establishes WebSocket connection to server
2. **Button Press**: User presses button on Device 1
3. **Capture**: Device 1 reads audio from microphone via I2S
4. **Transmit**: Device 1 sends binary audio data to server
5. **Relay**: Server broadcasts audio to all other connected devices
6. **Playback**: Devices 2, 3, etc. receive audio and play through speaker
7. **Button Release**: Device 1 stops transmitting

### LED Status Indicators

| Color  | Meaning                      |
|--------|------------------------------|
| Red    | Disconnected from server     |
| Green  | Connected and ready          |
| Blue   | Transmitting (talking)       |
| Yellow | Receiving audio from others  |

## Pin Configuration

The M5Stack Atom Echo uses these pins (DO NOT MODIFY):

| Pin  | Function           |
|------|--------------------|
| G19  | I2S Speaker BCK    |
| G22  | I2S Speaker DATA   |
| G23  | I2S Mic DATA       |
| G33  | I2S WS             |
| G39  | Button (active low)|

## Customization

### Device Naming

Edit `.env` before flashing each device:
```
DEVICE_NAME=Alice
```

### Audio Quality

Edit `include/config.h` (advanced):
```cpp
#define SAMPLE_RATE 16000       // 8000 or 16000
#define AUDIO_BUFFER_SIZE 512   // 256, 512, or 1024
```

### Multiple WiFi Networks

Add up to 3 networks in `.env` - device tries each in order:
```
WIFI_SSID_1=HomeNetwork
WIFI_PASSWORD_1=password1

WIFI_SSID_2=GrandmasHouse
WIFI_PASSWORD_2=password2
```

## Troubleshooting

### WiFi Won't Connect

- Check SSID and password in `.env`, then re-run `python configure.py` and reflash
- Ensure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
- Check signal strength
- Monitor serial output: `pio device monitor`

### WebSocket Connection Fails

- Verify server is running and accessible
- Check server IP address in `.env`
- Ensure firewall allows port 8080
- Test server health endpoint: `http://server-ip:8080/health`

### No Audio

- Check I2S initialization in serial output
- Verify button is working (LED changes color)
- Test with 2+ devices (need someone to transmit and receive)
- Check server logs to confirm audio data is being relayed

### Poor Audio Quality

- Reduce distance to WiFi router
- Lower sample rate to reduce bandwidth
- Check for WiFi interference
- Increase audio buffer size

### Button Not Responding

- M5Atom button is GPIO 39 (active low)
- Check button in M5.Btn.isPressed() debug output
- Ensure M5.update() is called in loop()

## Battery Life Optimization

For extended operation on USB power banks:

1. **Reduce WiFi Power**:
```cpp
WiFi.setSleep(WIFI_PS_MIN_MODEM);  // Add to setup()
```

2. **Lower Sample Rate**: Use 8000 Hz instead of 16000 Hz

3. **Deep Sleep When Idle**: Implement timeout sleep (advanced)

## Safety Considerations

- This is for kids, so keep server private or use authentication
- Audio is NOT encrypted by default
- Devices should only connect to trusted WiFi networks
- Consider adding volume limits for hearing protection

## Future Enhancements

- [ ] Add audio compression (Opus codec)
- [ ] Implement voice activation (VOX)
- [ ] Add multiple channel/group support
- [ ] Encrypt audio streams
- [ ] Battery level indicator
- [ ] Web dashboard for monitoring connected devices
- [ ] Recording/playback feature
- [ ] Text-to-speech announcements

## References

- [M5Stack Atom Echo Documentation](https://docs.m5stack.com/en/atom/atomecho)
- [M5Stack GitHub Repository](https://github.com/m5stack/ATOM-ECHO)
- [Wokwi ESP32 Simulator](https://wokwi.com/esp32)
- [ESP32 I2S Audio Guide](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/i2s.html)
- [WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)

## License

MIT License - feel free to modify and share!

## Contributing

Issues and pull requests welcome! This is a fun learning project for kids and parents.

---

**Have fun with your internet walkie-talkies! 📻✨**