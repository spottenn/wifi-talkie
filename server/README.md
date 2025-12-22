# WiFi Walkie-Talkie Server

WebSocket relay server for M5Stack Atom Echo walkie-talkie devices.

## Overview

This server acts as a central relay that:
- Accepts WebSocket connections from walkie-talkie devices
- Receives audio data from transmitting device
- Broadcasts audio to all other connected devices
- Tracks connection state and handles reconnections

## Installation

### Node.js Version

```bash
npm install
npm start
```

### Python Version

```bash
pip install websockets
python server.py
```

## Configuration

Default settings:
- **Port**: 8080
- **Path**: `/walkie`
- **Protocol**: WebSocket (ws://)

To change the port:

**Node.js:**
```bash
PORT=3000 npm start
```

**Python:**
```python
# Edit server.py
PORT = 3000
```

## Deployment Options

### Local Network (Home Use)

Run on any computer on your local network:

1. Start server: `npm start` or `python server.py`
2. Note your IP address (e.g., 192.168.1.100)
3. Configure devices with: `ws://192.168.1.100:8080`

**Pros**: Free, private, low latency
**Cons**: Devices must be on same WiFi network

### Raspberry Pi (Always-On Home Server)

```bash
# Install Node.js on Raspberry Pi
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Clone and run
git clone <your-repo>
cd wifi-talkie/server
npm install
npm start
```

**Auto-start on boot:**
```bash
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
ExecStart=/usr/bin/node server.js
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable walkie-server
sudo systemctl start walkie-server
```

### Cloud Hosting (Internet-Wide Access)

#### Railway.app (Recommended - Easy)

1. Create account at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Set root directory to `/server`
5. Railway auto-detects Node.js
6. Get your URL: `your-app.railway.app`
7. Configure devices with: `ws://your-app.railway.app:8080`

#### Render.com (Free Tier Available)

1. Create account at [render.com](https://render.com)
2. New Web Service → Connect repository
3. Settings:
   - **Root Directory**: `server`
   - **Build Command**: `npm install`
   - **Start Command**: `npm start`
4. Deploy and get URL

#### Heroku

```bash
# Install Heroku CLI
heroku login
heroku create your-walkie-server

# Deploy
git subtree push --prefix server heroku main
```

#### DigitalOcean / AWS / Google Cloud

Deploy as a standard Node.js or Python application. Make sure:
- Port 8080 is open in firewall
- WebSocket connections are allowed
- SSL/TLS if using wss:// (recommended for internet)

### Docker Deployment

```dockerfile
# Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY server.js ./
EXPOSE 8080
CMD ["node", "server.js"]
```

```bash
docker build -t walkie-server .
docker run -p 8080:8080 walkie-server
```

## Security Considerations

### For Local/Home Use
- Server binds to 0.0.0.0 (all interfaces) by default
- No authentication - any device can connect
- Audio is not encrypted
- **Recommendation**: Use on private home network only

### For Internet/Cloud Use

⚠️ **WARNING**: Default configuration has NO security!

**Recommended additions:**

1. **Add Authentication**:
```javascript
// Add to server.js
const API_KEY = process.env.API_KEY || 'change-me';

ws.on('message', (data) => {
  const msg = JSON.parse(data);
  if (!msg.apiKey || msg.apiKey !== API_KEY) {
    ws.close(1008, 'Unauthorized');
    return;
  }
  // ... rest of code
});
```

2. **Use WSS (Secure WebSocket)**:
```javascript
const https = require('https');
const fs = require('fs');

const server = https.createServer({
  cert: fs.readFileSync('cert.pem'),
  key: fs.readFileSync('key.pem')
});
```

3. **Rate Limiting**: Prevent abuse
4. **Connection Limits**: Max devices per "room"
5. **Firewall**: Restrict to known IP ranges

## Monitoring

### Health Check

```bash
curl http://localhost:8080/health
# Should return: OK
```

### View Connected Clients

The server logs show:
- Client connections/disconnections
- Number of connected clients
- Audio broadcasts
- Transmission events

### Prometheus Metrics (Advanced)

Add to server.js for monitoring:
```javascript
const prometheus = require('prom-client');
const register = new prometheus.Registry();

const clientsGauge = new prometheus.Gauge({
  name: 'walkie_connected_clients',
  help: 'Number of connected walkie-talkie clients'
});

register.registerMetric(clientsGauge);

// Update when clients connect/disconnect
clientsGauge.set(clients.size);
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8080
# Linux/Mac:
lsof -i :8080
# Windows:
netstat -ano | findstr :8080

# Kill it or use different port
PORT=8081 npm start
```

### Clients Can't Connect

1. **Check firewall**: Allow port 8080
2. **Check IP address**: Use `ifconfig` / `ipconfig`
3. **Test locally**: `ws://localhost:8080/walkie`
4. **Check server logs**: Should show "Server running on port 8080"

### High Latency

- **Reduce WiFi distance**: Move closer to router
- **Lower audio sample rate**: Edit device config to 8000 Hz
- **Check network**: Run `ping` to server
- **Server location**: Deploy closer to users geographically

### Memory Usage Growing

This can happen with many audio streams. Add cleanup:

```javascript
// Add to server.js
setInterval(() => {
  clients.forEach(client => {
    if (client.readyState === WebSocket.CLOSED) {
      clients.delete(client);
    }
  });
}, 60000); // Clean up every minute
```

## Message Protocol

### Text Messages (JSON)

**Register:**
```json
{
  "type": "register",
  "device": "Alice"
}
```

**Start Transmission:**
```json
{
  "type": "start_transmission"
}
```

**End Transmission:**
```json
{
  "type": "end_transmission"
}
```

### Binary Messages

Raw audio data (int16 PCM, 16kHz sample rate)

## Performance

**Expected capacity** (on modest hardware):
- ~10-20 concurrent devices
- ~1 Mbps bandwidth per transmitting device (at 16kHz)
- ~100ms latency on good network

**Optimization tips**:
- Use audio compression (Opus codec)
- Implement selective forwarding (groups/channels)
- Use UDP instead of TCP (requires different protocol)

## Development

### Run in Development Mode

```bash
npm run dev  # Uses nodemon for auto-restart
```

### Testing

Test with `wscat`:
```bash
npm install -g wscat
wscat -c ws://localhost:8080/walkie
```

Send test message:
```json
{"type": "register", "device": "test"}
```

## License

MIT License
