# Quick Start Guide

Get your WiFi walkie-talkies up and running in minutes!

## Prerequisites

- [ ] M5Stack Atom Echo devices (at least 2)
- [ ] USB-C cables for programming
- [ ] WiFi network (2.4GHz)
- [ ] Computer with Python or Node.js installed

## Step 1: Configure WiFi (5 minutes)

1. Open `include/config.h` in a text editor
2. Update these lines with your WiFi credentials:

```cpp
#define WIFI_SSID "YourWiFiName"
#define WIFI_PASSWORD "YourWiFiPassword"
```

3. Find your computer's IP address:
   - **Windows**: Run `ipconfig` in Command Prompt
   - **Mac/Linux**: Run `ifconfig` or `ip addr`

4. Update the server address (replace with your IP):

```cpp
#define WEBSOCKET_SERVER "ws://192.168.1.100"  // Your computer's IP
```

## Step 2: Start the Server (2 minutes)

Choose either Node.js or Python:

### Option A: Node.js
```bash
cd server
npm install
npm start
```

### Option B: Python
```bash
cd server
pip install websockets
python server.py
```

You should see: "WiFi Walkie-Talkie Server" and "Server running on port 8080"

**Keep this terminal window open!**

## Step 3: Install PlatformIO (One-time, 5 minutes)

```bash
pip install platformio
```

Or install the VSCode extension: "PlatformIO IDE"

## Step 4: Program Your Devices (5 minutes per device)

1. Connect M5Stack Atom Echo via USB-C
2. Build and upload:

```bash
pio run --target upload
```

3. Watch the LED:
   - **Red** = Connecting to WiFi
   - **Green** = Connected and ready!

4. Repeat for each device

## Step 5: Test It Out!

1. Press and hold the button on one device (LED turns **blue**)
2. Speak into it
3. Other devices should show **yellow** and play the audio
4. Release button to stop

## LED Status Guide

| Color | What it means |
|-------|---------------|
| 🔴 Red | Not connected - check WiFi/server |
| 🟢 Green | Connected - ready to use! |
| 🔵 Blue | Transmitting - you're talking |
| 🟡 Yellow | Receiving - someone else is talking |

## Troubleshooting

### Red LED won't turn green?

1. **Check WiFi credentials** in `include/config.h`
2. **Ensure 2.4GHz WiFi** (ESP32 doesn't support 5GHz)
3. **Check serial monitor**: `pio device monitor`

### Server won't start?

- **Port already in use?** Close other applications using port 8080
- **Check you're in server/ directory**: `cd server`

### No audio?

- **Need 2+ devices** to test audio
- **Check server terminal** - should show "Audio broadcasted to X clients"
- **Try speaking louder** - built-in mic is small

### Can't upload to device?

- **Install drivers**: FTDI drivers for M5Stack
- **Check USB cable** - some cables are power-only
- **Hold button during upload** if it fails

## What's Next?

- **Give devices names**: Edit `DEVICE_NAME` in config.h for each device
- **Adjust audio quality**: Change `SAMPLE_RATE` (8000 or 16000)
- **Deploy server to cloud**: See README.md for hosting options
- **Add USB battery**: Connect power bank for portable use

## Support

- Full documentation: See `README.md`
- M5Stack docs: https://docs.m5stack.com/en/atom/atomecho
- Issues: Create an issue in this repository

Have fun! 📻
