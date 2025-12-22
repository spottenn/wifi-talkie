#ifndef CONFIG_H
#define CONFIG_H

// Wi-Fi Configuration (hardcoded)
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// WebSocket Server Configuration
// Option 1: Use a free service like websocket.org test server for initial testing
// Option 2: Self-hosted server (see server/ directory)
#define WEBSOCKET_SERVER "ws://your-server-address"
#define WEBSOCKET_PORT 80
#define WEBSOCKET_PATH "/walkie"

// Audio Configuration
#define SAMPLE_RATE 16000
#define SAMPLE_BITS 16
#define AUDIO_BUFFER_SIZE 512

// Device Configuration
#define DEVICE_NAME "WalkieTalkie"
#define BUTTON_PIN 39  // M5Atom button pin

// Connection timeout (milliseconds)
#define WIFI_TIMEOUT 10000
#define RECONNECT_DELAY 5000

#endif // CONFIG_H
