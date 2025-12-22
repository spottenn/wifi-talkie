#include <M5Atom.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>
#include "config.h"

// Global objects
WebSocketsClient webSocket;
bool isConnected = false;
bool isTransmitting = false;
bool buttonPressed = false;

// Audio buffer
int16_t audioBuffer[AUDIO_BUFFER_SIZE];

// LED colors for status indication
const uint32_t COLOR_DISCONNECTED = 0xFF0000;  // Red
const uint32_t COLOR_CONNECTED = 0x00FF00;     // Green
const uint32_t COLOR_TRANSMITTING = 0x0000FF;  // Blue
const uint32_t COLOR_RECEIVING = 0xFFFF00;     // Yellow

// I2S configuration for microphone (input)
const i2s_config_t i2s_config_mic = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_PDM),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ALL_RIGHT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 2,
    .dma_buf_len = 128,
};

const i2s_pin_config_t pin_config_mic = {
    .bck_io_num = I2S_PIN_NO_CHANGE,
    .ws_io_num = 33,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = 23,
};

// I2S configuration for speaker (output)
const i2s_config_t i2s_config_spk = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 2,
    .dma_buf_len = 128,
};

const i2s_pin_config_t pin_config_spk = {
    .bck_io_num = 19,
    .ws_io_num = 33,
    .data_out_num = 22,
    .data_in_num = I2S_PIN_NO_CHANGE,
};

void setLEDColor(uint32_t color) {
    M5.dis.drawpix(0, color);
}

void setupI2S() {
    // Install and configure I2S driver for microphone
    i2s_driver_install(I2S_NUM_0, &i2s_config_mic, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config_mic);
    i2s_set_clk(I2S_NUM_0, SAMPLE_RATE, I2S_BITS_PER_SAMPLE_16BIT, I2S_CHANNEL_MONO);

    Serial.println("I2S initialized for microphone and speaker");
}

void connectWiFi() {
    Serial.print("Connecting to WiFi: ");
    Serial.println(WIFI_SSID);

    setLEDColor(COLOR_DISCONNECTED);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    unsigned long startAttempt = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < WIFI_TIMEOUT) {
        delay(500);
        Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected!");
        Serial.print("IP address: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\nWiFi connection failed!");
    }
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            Serial.println("WebSocket disconnected");
            isConnected = false;
            setLEDColor(COLOR_DISCONNECTED);
            break;

        case WStype_CONNECTED:
            Serial.println("WebSocket connected");
            isConnected = true;
            setLEDColor(COLOR_CONNECTED);

            // Send registration message
            {
                JsonDocument doc;
                doc["type"] = "register";
                doc["device"] = DEVICE_NAME;

                String output;
                serializeJson(doc, output);
                webSocket.sendTXT(output);
            }
            break;

        case WStype_TEXT:
            Serial.printf("Text message received: %s\n", payload);
            break;

        case WStype_BIN:
            // Received audio data from another walkie-talkie
            Serial.printf("Received audio data: %d bytes\n", length);

            // Show receiving status
            setLEDColor(COLOR_RECEIVING);

            // Play received audio through speaker
            size_t bytes_written;
            i2s_write(I2S_NUM_0, payload, length, &bytes_written, portMAX_DELAY);

            // Return to connected status after brief delay
            delay(50);
            if (!isTransmitting) {
                setLEDColor(COLOR_CONNECTED);
            }
            break;

        case WStype_ERROR:
            Serial.println("WebSocket error");
            break;

        case WStype_PING:
        case WStype_PONG:
            break;
    }
}

void connectWebSocket() {
    Serial.println("Connecting to WebSocket server...");

    // Parse WebSocket URL
    String wsUrl = String(WEBSOCKET_SERVER);
    wsUrl.replace("ws://", "");
    wsUrl.replace("wss://", "");

    String host = wsUrl;
    if (host.indexOf(':') > 0) {
        host = host.substring(0, host.indexOf(':'));
    }
    if (host.indexOf('/') > 0) {
        host = host.substring(0, host.indexOf('/'));
    }

    webSocket.begin(host, WEBSOCKET_PORT, WEBSOCKET_PATH);
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(RECONNECT_DELAY);
}

void transmitAudio() {
    size_t bytes_read;

    // Read audio from microphone
    i2s_read(I2S_NUM_0, audioBuffer, sizeof(audioBuffer), &bytes_read, portMAX_DELAY);

    if (bytes_read > 0) {
        // Send audio data to server
        webSocket.sendBIN((uint8_t*)audioBuffer, bytes_read);
        Serial.printf("Transmitted %d bytes of audio\n", bytes_read);
    }
}

void setup() {
    // Initialize M5Atom
    M5.begin(true, false, true);  // Serial, I2C, Display

    Serial.println("\n=== WiFi Walkie-Talkie Starting ===");

    // Set initial LED color
    setLEDColor(COLOR_DISCONNECTED);

    // Initialize I2S for audio
    setupI2S();

    // Connect to WiFi
    connectWiFi();

    // Connect to WebSocket server
    if (WiFi.status() == WL_CONNECTED) {
        connectWebSocket();
    }

    Serial.println("Setup complete!");
}

void loop() {
    M5.update();

    // Handle WebSocket
    if (isConnected) {
        webSocket.loop();
    } else if (WiFi.status() == WL_CONNECTED) {
        // Try to reconnect WebSocket
        static unsigned long lastReconnect = 0;
        if (millis() - lastReconnect > RECONNECT_DELAY) {
            connectWebSocket();
            lastReconnect = millis();
        }
    } else {
        // Try to reconnect WiFi
        static unsigned long lastWiFiReconnect = 0;
        if (millis() - lastWiFiReconnect > RECONNECT_DELAY) {
            connectWiFi();
            lastWiFiReconnect = millis();
        }
    }

    // Check button state (M5Atom button is active low)
    bool currentButtonState = M5.Btn.isPressed();

    if (currentButtonState && !buttonPressed) {
        // Button just pressed - start transmitting
        buttonPressed = true;
        if (isConnected) {
            isTransmitting = true;
            setLEDColor(COLOR_TRANSMITTING);
            Serial.println("Transmitting...");

            // Send start transmission message
            JsonDocument doc;
            doc["type"] = "start_transmission";
            String output;
            serializeJson(doc, output);
            webSocket.sendTXT(output);
        }
    } else if (!currentButtonState && buttonPressed) {
        // Button just released - stop transmitting
        buttonPressed = false;
        if (isTransmitting) {
            isTransmitting = false;
            setLEDColor(COLOR_CONNECTED);
            Serial.println("Transmission ended");

            // Send end transmission message
            JsonDocument doc;
            doc["type"] = "end_transmission";
            String output;
            serializeJson(doc, output);
            webSocket.sendTXT(output);
        }
    }

    // If transmitting, continuously send audio
    if (isTransmitting && isConnected) {
        transmitAudio();
    }

    delay(10);  // Small delay to prevent watchdog issues
}
