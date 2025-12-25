# WiFi Walkie-Talkie Server

WebSocket relay server for M5Stack Atom Echo walkie-talkie devices.

## Quick Start

```bash
pip install websockets
python server.py
```

Server runs on `ws://0.0.0.0:8080/walkie`

## Features

- Relays audio between all connected devices
- Records transmissions to `recordings/*.wav`
- Logs audio quality metrics

## Configuration

Edit `server.py` to change port:
```python
PORT = 8080
```

## Deployment

### Local Network
1. Run `python server.py` on any computer
2. Note your IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
3. Configure devices with: `ws://YOUR_IP:8080`

### Raspberry Pi (Always-On)

```bash
# Install Python dependencies
pip install websockets

# Create systemd service
sudo nano /etc/systemd/system/walkie-server.service
```

```ini
[Unit]
Description=WiFi Walkie-Talkie Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wifi-talkie/server
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable walkie-server
sudo systemctl start walkie-server
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install websockets
COPY server.py .
EXPOSE 8080
CMD ["python", "server.py"]
```

```bash
docker build -t walkie-server .
docker run -p 8080:8080 walkie-server
```

## Message Protocol

### JSON Control Messages
```json
{"type": "register", "device": "Alice"}
{"type": "start_transmission"}
{"type": "end_transmission"}
```

### Binary Messages
Raw audio: int16 PCM, 16kHz sample rate

## Troubleshooting

### Port in use
```bash
# Find process
netstat -ano | findstr :8080  # Windows
lsof -i :8080                 # Linux/Mac
```

### Clients can't connect
1. Check firewall allows port 8080
2. Verify IP address
3. Check server logs

## Security Note

Default config has no authentication - use on trusted home network only.
