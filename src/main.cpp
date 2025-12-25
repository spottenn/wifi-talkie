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
bool isSpeakerMode = false;  // Track current I2S mode

// Debug transmission control (serial commands)
bool debugTransmitting = false;
unsigned long debugTransmitStart = 0;
const unsigned long DEBUG_TRANSMIT_DURATION = 3000;  // 3 seconds

// Speaker timeout - auto-switch back to mic after audio stops
unsigned long lastAudioReceived = 0;
const unsigned long SPEAKER_TIMEOUT_MS = 300;  // Switch back to mic after 300ms of silence

// Audio gain for PDM microphone (raw PDM is very quiet)
const int16_t AUDIO_GAIN = 8;  // 8x amplification

// Audio buffer
int16_t audioBuffer[AUDIO_BUFFER_SIZE];
int16_t silenceBuffer[AUDIO_BUFFER_SIZE] = {0};  // Pre-filled silence for flushing

// LED colors for status indication
const uint32_t COLOR_DISCONNECTED = 0xFF0000;  // Red
const uint32_t COLOR_CONNECTED = 0x00FF00;     // Green
const uint32_t COLOR_TRANSMITTING = 0x0000FF;  // Blue
const uint32_t COLOR_RECEIVING = 0xFFFF00;     // Yellow

// I2S configuration for microphone (input)
// Increased DMA buffers: 8 x 256 = 2048 samples = 128ms at 16kHz (was 16ms)
const i2s_config_t i2s_config_mic = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_PDM),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ALL_RIGHT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 256,
};

const i2s_pin_config_t pin_config_mic = {
    .bck_io_num = I2S_PIN_NO_CHANGE,
    .ws_io_num = 33,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = 23,
};

// I2S configuration for speaker (output)
// Increased DMA buffers: 8 x 256 = 2048 samples = 128ms at 16kHz (was 16ms)
const i2s_config_t i2s_config_spk = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 256,
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

void flushSpeakerWithSilence() {
    // Write silence to flush any residual audio in DMA buffers
    // This prevents buzzing after transmission ends
    size_t bytes_written;
    for (int i = 0; i < 4; i++) {  // Flush multiple times to clear all buffers
        i2s_write(I2S_NUM_0, silenceBuffer, sizeof(silenceBuffer), &bytes_written, 10);
    }
    i2s_zero_dma_buffer(I2S_NUM_0);  // Also zero the DMA buffer directly
}

void switchToMicMode() {
    if (!isSpeakerMode) return;  // Already in mic mode

    // Flush speaker with silence before switching to prevent buzzing
    flushSpeakerWithSilence();

    i2s_driver_uninstall(I2S_NUM_0);
    i2s_driver_install(I2S_NUM_0, &i2s_config_mic, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config_mic);
    i2s_set_clk(I2S_NUM_0, SAMPLE_RATE, I2S_BITS_PER_SAMPLE_16BIT, I2S_CHANNEL_MONO);
    isSpeakerMode = false;
    Serial.printf("[%s] Switched to MIC mode\n", DEVICE_NAME);
}

void switchToSpeakerMode() {
    if (isSpeakerMode) return;  // Already in speaker mode

    i2s_driver_uninstall(I2S_NUM_0);
    i2s_driver_install(I2S_NUM_0, &i2s_config_spk, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config_spk);
    i2s_set_clk(I2S_NUM_0, SAMPLE_RATE, I2S_BITS_PER_SAMPLE_16BIT, I2S_CHANNEL_MONO);
    isSpeakerMode = true;
    Serial.printf("[%s] Switched to SPEAKER mode\n", DEVICE_NAME);
}

void setupI2S() {
    // Start in microphone mode (for transmitting)
    i2s_driver_install(I2S_NUM_0, &i2s_config_mic, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config_mic);
    i2s_set_clk(I2S_NUM_0, SAMPLE_RATE, I2S_BITS_PER_SAMPLE_16BIT, I2S_CHANNEL_MONO);
    isSpeakerMode = false;

    Serial.println("I2S initialized in MIC mode (will switch for playback)");
}

void connectWiFi() {
    setLEDColor(COLOR_DISCONNECTED);

    // List of WiFi networks to try (in order)
    const char* networks[][2] = {
        {WIFI_SSID_1, WIFI_PASSWORD_1},
        {WIFI_SSID_2, WIFI_PASSWORD_2},
        {WIFI_SSID_3, WIFI_PASSWORD_3}
    };

    // Try each network
    for (int i = 0; i < 3; i++) {
        // Skip empty network names
        if (strlen(networks[i][0]) == 0) {
            continue;
        }

        Serial.print("Trying WiFi network: ");
        Serial.println(networks[i][0]);

        WiFi.begin(networks[i][0], networks[i][1]);

        unsigned long startAttempt = millis();
        while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < WIFI_TIMEOUT) {
            delay(500);
            Serial.print(".");
        }

        if (WiFi.status() == WL_CONNECTED) {
            Serial.println("\nWiFi connected!");
            Serial.print("Network: ");
            Serial.println(networks[i][0]);
            Serial.print("IP address: ");
            Serial.println(WiFi.localIP());
            return;  // Successfully connected
        } else {
            Serial.println("\nFailed to connect to this network.");
        }
    }

    Serial.println("ERROR: Could not connect to any WiFi network!");
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
            if (!isTransmitting && !debugTransmitting) {
                // Only play if we're not transmitting
                setLEDColor(COLOR_RECEIVING);

                // Switch to speaker mode and play
                switchToSpeakerMode();
                size_t bytes_written;
                i2s_write(I2S_NUM_0, payload, length, &bytes_written, portMAX_DELAY);

                // Track when we last received audio for timeout-based mode switching
                lastAudioReceived = millis();

                Serial.printf("[%s] Played audio: %d bytes\n", DEVICE_NAME, length);
                // Don't immediately switch LED - let timeout handle it
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
    Serial.printf("DEBUG: Full server URL: %s\n", WEBSOCKET_SERVER);
    Serial.printf("DEBUG: Device IP: %s\n", WiFi.localIP().toString().c_str());

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

    Serial.printf("DEBUG: Parsed host: %s\n", host.c_str());
    Serial.printf("DEBUG: Port: %d, Path: %s\n", WEBSOCKET_PORT, WEBSOCKET_PATH);

    webSocket.begin(host, WEBSOCKET_PORT, WEBSOCKET_PATH);
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(RECONNECT_DELAY);
}

void transmitAudio() {
    size_t bytes_read;

    // Read audio from microphone
    i2s_read(I2S_NUM_0, audioBuffer, sizeof(audioBuffer), &bytes_read, portMAX_DELAY);

    if (bytes_read > 0) {
        // Apply gain amplification - PDM microphone output is very quiet
        int numSamples = bytes_read / sizeof(int16_t);
        for (int i = 0; i < numSamples; i++) {
            int32_t amplified = (int32_t)audioBuffer[i] * AUDIO_GAIN;
            // Clip to prevent overflow
            if (amplified > 32767) amplified = 32767;
            if (amplified < -32768) amplified = -32768;
            audioBuffer[i] = (int16_t)amplified;
        }

        // Send audio data to server
        webSocket.sendBIN((uint8_t*)audioBuffer, bytes_read);
        Serial.printf("[%s] Transmitted %d bytes of audio (gain=%d)\n", DEVICE_NAME, bytes_read, AUDIO_GAIN);
    }
}

void setup() {
    // Initialize serial FIRST for debugging
    Serial.begin(115200);
    delay(1000);  // Give serial time to initialize
    Serial.println("\n\n========================================");
    Serial.println("DEBUG: Serial initialized");
    Serial.println("DEBUG: About to call M5.begin()...");

    // Initialize M5Atom
    M5.begin(true, false, true);  // Serial, I2C, Display
    Serial.println("DEBUG: M5.begin() completed");

    Serial.println("\n=== WiFi Walkie-Talkie Starting ===");
    Serial.printf("=== DEVICE: %s ===\n", DEVICE_NAME);

    // Set initial LED color
    Serial.println("DEBUG: Setting LED color...");
    setLEDColor(COLOR_DISCONNECTED);
    Serial.println("DEBUG: LED set to red (disconnected)");

    // Initialize I2S for audio
    Serial.println("DEBUG: About to initialize I2S...");
    setupI2S();
    Serial.println("DEBUG: I2S initialized");

    // Connect to WiFi
    Serial.println("DEBUG: About to connect WiFi...");
    Serial.printf("DEBUG: SSID = %s\n", WIFI_SSID_1);
    connectWiFi();

    // Connect to WebSocket server
    if (WiFi.status() == WL_CONNECTED) {
        connectWebSocket();
    }

    Serial.println("Setup complete!");
}

// Helper functions for debug transmission
void startDebugTransmission() {
    if (!isConnected) {
        Serial.println("[DEBUG] Cannot transmit - not connected");
        return;
    }
    if (debugTransmitting || isTransmitting) {
        Serial.println("[DEBUG] Already transmitting");
        return;
    }

    debugTransmitting = true;
    debugTransmitStart = millis();
    switchToMicMode();
    setLEDColor(COLOR_TRANSMITTING);
    Serial.printf("[DEBUG] Started %dms test transmission\n", DEBUG_TRANSMIT_DURATION);

    // Send start transmission message
    JsonDocument doc;
    doc["type"] = "start_transmission";
    doc["debug"] = true;
    String output;
    serializeJson(doc, output);
    webSocket.sendTXT(output);
}

void stopDebugTransmission() {
    if (!debugTransmitting) return;

    debugTransmitting = false;
    setLEDColor(COLOR_CONNECTED);
    Serial.println("[DEBUG] Stopped test transmission");

    // Send end transmission message
    JsonDocument doc;
    doc["type"] = "end_transmission";
    doc["debug"] = true;
    String output;
    serializeJson(doc, output);
    webSocket.sendTXT(output);
}

void loop() {
    M5.update();

    // Handle WebSocket - must call loop() even when connecting!
    if (WiFi.status() == WL_CONNECTED) {
        webSocket.loop();  // Process WebSocket events (including connection handshake)

        if (!isConnected) {
            // Try to reconnect WebSocket if disconnected
            static unsigned long lastReconnect = 0;
            if (millis() - lastReconnect > RECONNECT_DELAY) {
                connectWebSocket();
                lastReconnect = millis();
            }
        }
    } else {
        // Try to reconnect WiFi
        static unsigned long lastWiFiReconnect = 0;
        if (millis() - lastWiFiReconnect > RECONNECT_DELAY) {
            connectWiFi();
            lastWiFiReconnect = millis();
        }
    }

    // === DEBUG SERIAL COMMANDS ===
    // T = Start 3-second test transmission
    // S = Stop transmission
    // ? = Print status
    if (Serial.available()) {
        char cmd = Serial.read();
        switch (cmd) {
            case 'T':
            case 't':
                startDebugTransmission();
                break;
            case 'S':
            case 's':
                stopDebugTransmission();
                break;
            case '?':
                Serial.printf("[STATUS] Connected=%d, TX=%d, DebugTX=%d, SpeakerMode=%d\n",
                    isConnected, isTransmitting, debugTransmitting, isSpeakerMode);
                break;
        }
    }

    // === DEBUG TRANSMISSION TIMEOUT ===
    if (debugTransmitting && (millis() - debugTransmitStart >= DEBUG_TRANSMIT_DURATION)) {
        stopDebugTransmission();
    }

    // === SPEAKER TIMEOUT - Auto-switch back to mic mode ===
    // After receiving audio, wait for timeout then switch back to mic
    // This prevents buzzing and prepares device for transmitting
    if (isSpeakerMode && !isTransmitting && !debugTransmitting) {
        if (lastAudioReceived > 0 && (millis() - lastAudioReceived > SPEAKER_TIMEOUT_MS)) {
            Serial.println("[AUTO] Speaker timeout - switching to mic mode");
            switchToMicMode();
            setLEDColor(COLOR_CONNECTED);
            lastAudioReceived = 0;  // Reset to avoid repeated switches
        }
    }

    // Check button state (M5Atom button is active low)
    bool currentButtonState = M5.Btn.isPressed();

    if (currentButtonState && !buttonPressed) {
        // Button just pressed - start transmitting
        buttonPressed = true;
        if (isConnected && !debugTransmitting) {
            isTransmitting = true;
            switchToMicMode();  // Switch I2S to microphone
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

    // If transmitting (button or debug), continuously send audio
    if ((isTransmitting || debugTransmitting) && isConnected) {
        transmitAudio();
    }

    delay(10);  // Small delay to prevent watchdog issues
}
