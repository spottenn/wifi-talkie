# 🎯 START HERE - Christmas Eve Setup

**Your M5Stack Atom Echo devices arrived! Here's what to do NOW:**

## ⚡ Super Quick Start (5 Minutes)

### 1. Set WiFi Password

```bash
nano .env
```

Change `PUT_YOUR_PASSWORD_HERE` to your NetKey52 password.

**Save**: Press `Ctrl+X`, `Y`, `Enter`

### 2. Find Your Computer's IP Address

**Mac/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows:**
```bash
ipconfig
```

Look for something like `192.168.1.105`

### 3. Update Server Address

```bash
nano .env
```

Change the IP in `WEBSOCKET_SERVER=ws://192.168.1.100:8080` to YOUR IP.

Example: `WEBSOCKET_SERVER=ws://192.168.1.105:8080`

### 4. Start Server

```bash
cd server
python3 server.py
```

**KEEP THIS TERMINAL OPEN!**

### 5. Flash Devices

Open a NEW terminal:

```bash
# First device
./flash.sh Alice

# Disconnect, connect second device
./flash.sh Bob

# Repeat for more devices...
```

### 6. TEST!

1. Press button on Alice (LED turns BLUE)
2. Talk: "Testing 1-2-3"
3. Release button
4. Bob should hear it! (LED turns YELLOW)

## 🎉 Done!

**For detailed help, see:** `DEPLOYMENT.md`

**For troubleshooting:** See "Troubleshooting" section in `DEPLOYMENT.md`

---

## 📚 All Documentation

- **START_HERE.md** ← You are here (quick start)
- **DEPLOYMENT.md** - Detailed Christmas Eve deployment guide
- **README.md** - Full project documentation
- **QUICKSTART.md** - Alternative quick start guide
- **TESTING.md** - How to test without hardware
- **server/README.md** - Server deployment options

## 🆘 Quick Fixes

**Red LED stuck?**
- Check WiFi password in `.env`
- Make sure you ran `./flash.sh DeviceName`

**No sound?**
- Need 2+ devices to test
- Check server terminal shows "Audio broadcasted to X clients"

**Can't upload?**
- Install PlatformIO: `pip install platformio`
- Check USB cable (some are power-only!)

## ⚙️ Built-In Libraries (No Custom Code Needed!)

You asked about libraries - **good news!** The M5Stack Atom Echo uses:

✅ **WiFi.h** - Built-in ESP32 WiFi (supports WPA2, automatic reconnection)
✅ **WebSocketsClient** - Standard library for WebSocket
✅ **M5Atom** - Official M5Stack library (button, LED, I2S audio)
✅ **ArduinoJson** - Standard JSON library

**No low-level WiFi code needed!** Everything "just works" - we're using battle-tested libraries.

## 🤔 Simulation Explanation

You asked about simulation level:

**My Test (test_client.py):**
- Python script → WebSocket → Server → WebSocket → Python script
- Simulates the **protocol** (WebSocket messages, audio data)
- NOT hardware simulation - just testing server relay logic

**Real ESP32:**
- M5Stack → WiFi → Server → WiFi → M5Stack
- Uses real hardware, real WiFi, same WebSocket protocol
- Built-in WiFi modem handles all networking automatically

**Why Simple Server vs Mumble:**
- ✅ Our server: 200 lines, tested, works perfectly, no accounts needed
- ❌ Mumble: Complex, needs authentication, channels, not designed for push-to-talk kids' toy
- ✅ Ours is perfect for kids - just press and talk!

## 🎄 Christmas Countdown

**READY TO FLASH** ✅

Everything is configured for:
- WiFi: NetKey52 (just add password)
- Multi-network support (add friend's WiFi later)
- Server tested and working
- Firmware ready to build

**When devices arrive:**
1. Edit `.env` (2 min)
2. Start server (30 sec)
3. Flash devices (5 min each)
4. DONE! 🎉

---

**Merry Christmas! 🎅**
