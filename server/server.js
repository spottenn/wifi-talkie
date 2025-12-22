/**
 * WiFi Walkie-Talkie WebSocket Server
 *
 * This server relays audio data between all connected walkie-talkie devices.
 * When one device transmits, all other devices receive the audio.
 */

const WebSocket = require('ws');
const http = require('http');

const PORT = process.env.PORT || 8080;

// Create HTTP server
const server = http.createServer((req, res) => {
    if (req.url === '/health') {
        res.writeHead(200);
        res.end('OK');
    } else {
        res.writeHead(200);
        res.end('WiFi Walkie-Talkie Server');
    }
});

// Create WebSocket server
const wss = new WebSocket.Server({ server, path: '/walkie' });

// Store connected clients
const clients = new Set();
let transmittingClient = null;

wss.on('connection', (ws, req) => {
    const clientIP = req.socket.remoteAddress;
    console.log(`New client connected from ${clientIP}`);

    // Add client to set
    clients.add(ws);
    console.log(`Total clients: ${clients.size}`);

    // Handle messages from client
    ws.on('message', (data, isBinary) => {
        if (isBinary) {
            // Binary data = audio
            console.log(`Received audio data: ${data.length} bytes from ${clientIP}`);

            // Broadcast audio to all other clients
            let sentCount = 0;
            clients.forEach(client => {
                if (client !== ws && client.readyState === WebSocket.OPEN) {
                    try {
                        client.send(data, { binary: true });
                        sentCount++;
                    } catch (err) {
                        console.error(`Error sending to client: ${err.message}`);
                    }
                }
            });

            console.log(`Audio broadcasted to ${sentCount} clients`);
        } else {
            // Text data = control messages
            try {
                const message = JSON.parse(data);
                console.log(`Received message from ${clientIP}:`, message);

                switch (message.type) {
                    case 'register':
                        console.log(`Client registered as: ${message.device}`);
                        ws.deviceName = message.device;

                        // Send confirmation
                        ws.send(JSON.stringify({
                            type: 'registered',
                            clients: clients.size
                        }));
                        break;

                    case 'start_transmission':
                        transmittingClient = ws;
                        console.log(`${ws.deviceName || clientIP} started transmitting`);

                        // Notify other clients
                        broadcastMessage({
                            type: 'transmission_started',
                            device: ws.deviceName || 'unknown'
                        }, ws);
                        break;

                    case 'end_transmission':
                        if (transmittingClient === ws) {
                            transmittingClient = null;
                        }
                        console.log(`${ws.deviceName || clientIP} stopped transmitting`);

                        // Notify other clients
                        broadcastMessage({
                            type: 'transmission_ended',
                            device: ws.deviceName || 'unknown'
                        }, ws);
                        break;

                    default:
                        console.log(`Unknown message type: ${message.type}`);
                }
            } catch (err) {
                console.error(`Error parsing message: ${err.message}`);
            }
        }
    });

    // Handle client disconnect
    ws.on('close', () => {
        clients.delete(ws);
        if (transmittingClient === ws) {
            transmittingClient = null;
        }
        console.log(`Client disconnected from ${clientIP}. Total clients: ${clients.size}`);
    });

    // Handle errors
    ws.on('error', (err) => {
        console.error(`WebSocket error from ${clientIP}: ${err.message}`);
    });

    // Send welcome message
    ws.send(JSON.stringify({
        type: 'welcome',
        message: 'Connected to WiFi Walkie-Talkie server',
        clients: clients.size
    }));
});

// Helper function to broadcast messages
function broadcastMessage(message, exclude = null) {
    const messageStr = JSON.stringify(message);
    clients.forEach(client => {
        if (client !== exclude && client.readyState === WebSocket.OPEN) {
            try {
                client.send(messageStr);
            } catch (err) {
                console.error(`Error broadcasting: ${err.message}`);
            }
        }
    });
}

// Start server
server.listen(PORT, () => {
    console.log(`\n========================================`);
    console.log(`WiFi Walkie-Talkie Server`);
    console.log(`========================================`);
    console.log(`Server running on port ${PORT}`);
    console.log(`WebSocket endpoint: ws://localhost:${PORT}/walkie`);
    console.log(`Health check: http://localhost:${PORT}/health`);
    console.log(`========================================\n`);
});

// Handle shutdown gracefully
process.on('SIGTERM', () => {
    console.log('SIGTERM received, closing server...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});
