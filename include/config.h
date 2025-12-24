#ifndef CONFIG_H
#define CONFIG_H

// Include local configuration if it exists (generated from .env file)
// This file is in .gitignore and contains WiFi passwords
#if __has_include("config_local.h")
#include "config_local.h"
#endif

// Default Wi-Fi Configuration (will be overridden by config_local.h)
#ifndef WIFI_SSID_1
#define WIFI_SSID_1 "NetKey52"
#endif

#ifndef WIFI_PASSWORD_1
#define WIFI_PASSWORD_1 "CHANGE_ME"
#endif

// Additional WiFi networks (optional - for visiting friends)
#ifndef WIFI_SSID_2
#define WIFI_SSID_2 ""
#endif

#ifndef WIFI_PASSWORD_2
#define WIFI_PASSWORD_2 ""
#endif

#ifndef WIFI_SSID_3
#define WIFI_SSID_3 ""
#endif

#ifndef WIFI_PASSWORD_3
#define WIFI_PASSWORD_3 ""
#endif

// WebSocket Server Configuration
#ifndef WEBSOCKET_SERVER
#define WEBSOCKET_SERVER "ws://192.168.1.100"
#endif

#ifndef WEBSOCKET_PORT
#define WEBSOCKET_PORT 8080
#endif

#ifndef WEBSOCKET_PATH
#define WEBSOCKET_PATH "/walkie"
#endif

// Device Configuration
#ifndef DEVICE_NAME
#define DEVICE_NAME "WalkieTalkie"
#endif

// Audio Configuration
#define SAMPLE_RATE 16000
#define SAMPLE_BITS 16
#define AUDIO_BUFFER_SIZE 512

// Hardware Configuration
#define BUTTON_PIN 39  // M5Atom button pin

// Connection timeout (milliseconds)
#define WIFI_TIMEOUT 10000
#define RECONNECT_DELAY 5000

#endif // CONFIG_H
