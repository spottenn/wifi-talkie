# 🎄 Christmas Eve Deployment Guide

**Get your WiFi walkie-talkies working in 15 minutes!**

## 📋 What You Need

- ✅ M5Stack Atom Echo devices (arrived!)
- ✅ USB-C cables for each device
- ✅ Computer with this code
- ✅ WiFi network: **NetKey52**
- ✅ WiFi password (you'll add this)

## 🚀 Quick Start (3 Steps!)

### Step 1: Set Your WiFi Password (2 minutes)

Edit the `.env` file and add your NetKey52 password:

```bash
nano .env
```

Change this line:
```
WIFI_PASSWORD_1=PUT_YOUR_PASSWORD_HERE
```

To your actual password:
```
WIFI_PASSWORD_1=your_real_password
```

**Save and exit**: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 2: Start the Server (1 minute)

Open a terminal and start the relay server:

```bash
cd server
python3 server.py
```

**Keep this terminal open!** You should see:
```
========================================
WiFi Walkie-Talkie Server
========================================
Starting server on 0.0.0.0:8080
```

**Note your computer's IP address** (you'll need it):
- **Mac/Linux**: Run `ifconfig | grep "inet " | grep -v 127.0.0.1`
- **Windows**: Run `ipconfig` and look for "IPv4 Address"

Example: `192.168.1.105`

### Step 3: Update Server Address (1 minute)

Edit `.env` again and update the server IP:

```bash
nano .env
```

Change:
```
WEBSOCKET_SERVER=ws://192.168.1.100:8080
```

To your computer's IP:
```
WEBSOCKET_SERVER=ws://192.168.1.105:8080
```

Save and exit.

## 📱 Flash Your Devices (5 minutes per device)

### Device 1 (e.g., "Alice")

1. **Connect** M5Stack Atom Echo via USB-C
2. **Run**:
   ```bash
   ./flash.sh Alice
   ```
3. **Wait** for upload to complete (~1 minute)
4. **Watch the LED**:
   - 🔴 Red = Connecting to WiFi...
   - 🟢 Green = Connected and ready!

### Device 2 (e.g., "Bob")

1. **Disconnect** Alice
2. **Connect** second device
3. **Run**:
   ```bash
   ./flash.sh Bob
   ```
4. **Wait** for green LED

### More Devices?

Repeat for each device with different names:
```bash
./flash.sh Charlie
./flash.sh Emma
./flash.sh Max
```

## ✅ Test It!

1. **Pick up Device 1** (Alice)
2. **Press and hold** the button - LED turns BLUE
3. **Speak**: "Testing, testing, 1-2-3"
4. **Release** button
5. **Device 2** (Bob) should:
   - LED turns YELLOW while receiving
   - **Play your voice** through speaker!

## 🎉 Done!

Your walkie-talkies are ready! The kids can now:
- Press button to talk (blue LED)
- Release button to listen
- Hear when others are talking (yellow LED)

## 📊 LED Status Guide

| Color | Meaning |
|-------|---------|
| 🔴 Red | Not connected - check WiFi/server |
| 🟢 Green | Connected - ready to use! |
| 🔵 Blue | Transmitting - you're talking |
| 🟡 Yellow | Receiving - someone else is talking |

## 🔧 Troubleshooting

### Red LED won't turn green?

**Check WiFi password:**
```bash
nano .env
# Verify WIFI_PASSWORD_1 is correct
```

**Reflash the device:**
```bash
./flash.sh Alice
```

**Check server is running:**
- Look at server terminal - should show "server listening on 0.0.0.0:8080"

### No audio received?

**Need 2+ devices:**
- You need at least 2 walkie-talkies to test audio
- One to talk, one to listen

**Check server logs:**
- Server terminal should show "Audio broadcasted to X clients"
- If it shows "0 clients", check WiFi connection

**Test button:**
```bash
# Connect device via USB
pio device monitor
# Press button - should see "Transmitting..." in logs
```

### Can't upload firmware?

**Install USB drivers:**
- Mac: Should work automatically
- Windows: Install [CP210x drivers](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
- Linux: Run `sudo usermod -a -G dialout $USER` then logout/login

**Try different USB cable:**
- Some cables are power-only!
- Use a data cable

**Press and hold button during upload:**
- Hold button on M5Stack while connecting USB

## 🏠 Adding Other Family Networks

When visiting friends, add their WiFi:

1. **Edit .env**:
   ```bash
   nano .env
   ```

2. **Add network**:
   ```
   WIFI_SSID_2=FriendHouse_WiFi
   WIFI_PASSWORD_2=their_password
   ```

3. **Reflash all devices**:
   ```bash
   ./flash.sh Alice
   ./flash.sh Bob
   # etc...
   ```

The walkie-talkies will automatically try networks in order:
1. NetKey52 (your home)
2. Friend's network
3. Third network (if configured)

## 🌐 Using Away from Home

### Option 1: Deploy Server to Cloud

See `server/README.md` for:
- Railway.app (easiest, free)
- Heroku
- Your own VPS

Update `.env`:
```
WEBSOCKET_SERVER=ws://your-server.railway.app:8080
```

### Option 2: Same WiFi Network

Kids must all be on same WiFi network (e.g., at friend's house):
- Bring laptop with server running
- All devices connect to friend's WiFi
- Server relays between them

## 📝 Device Name Ideas

- **Kids**: Alice, Bob, Charlie, Emma, Max, Lily
- **Funny**: RedLeader, BlueLeader, GreenGoblin
- **Themed**: Elsa, Anna, Olaf (Frozen theme)
- **Simple**: Walkie1, Walkie2, Walkie3

## 💾 Backup Configuration

Save your `.env` file somewhere safe:
```bash
cp .env .env.backup
```

## 🔋 Battery Power

To use with USB power banks:
1. **Flash device** via USB from computer
2. **Disconnect** from computer
3. **Connect** to USB power bank
4. **Power on** - should auto-connect to WiFi!

Power banks tested: Any 5V USB power bank works great.

## 🎁 Gift Wrapping Tips

If giving as gifts:
1. **Flash devices** before wrapping
2. **Include instruction card**:
   ```
   1. Turn on (plug in USB battery)
   2. Wait for GREEN light
   3. Press button to talk (BLUE)
   4. Release to hear friends (YELLOW)
   ```
3. **Include extra USB-C cable**
4. **Pre-charge power banks**

## 📞 Support

**Server not starting?**
```bash
pip install websockets
python3 server/server.py
```

**Build errors?**
```bash
pip install platformio
pio run
```

**Everything broken?**
1. Check `.env` file has correct password
2. Make sure server is running (don't close terminal!)
3. Devices should connect automatically when powered on

## 🎊 Have Fun!

The walkie-talkies are ready for Christmas! The kids will love them.

**Pro tip**: Test one transmission yourself before giving to kids so you know it works!

---

Merry Christmas! 🎄
