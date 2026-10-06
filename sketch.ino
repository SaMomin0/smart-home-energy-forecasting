/**
 * ============================================================================
 * AI FOR IOT CAPSTONE PROJECT - PHASE 1
 * Project Title : AI-Based Smart Home Energy Consumption Forecasting &
 *                 Wasteful Usage Detection
 * Focus         : Virtual Smart Home IoT Simulator (Wokwi + ESP32)
 * File          : sketch.ino
 * ============================================================================
 * Features:
 *   1. Environmental Sensing: DHT22 (Temperature & Humidity)
 *   2. Motion & Occupancy   : PIR Sensor
 *   3. Ambient Light Level  : LDR / Photoresistor (ADC1 GPIO 34)
 *   4. Household Appliances : 7 Discrete Appliances with Rated Wattages
 *   5. Physical Controls    : 7 Push Buttons with Software Debounce
 *   6. Visual Status        : 7 Color-Coded LEDs reflecting Appliance States
 *   7. Local Display        : SSD1306 128x64 I2C OLED (Cycling Telemetry Pages)
 *   8. Deterministic Power  : Real-time Wattage Summation (No Mocked Values)
 *   9. IoT-Level Logic      : Rule-Based Waste & High-Load Anomaly Flags
 *  10. MQTT Connectivity    : Non-blocking Auto-Reconnection & JSON Telemetry
 *  11. Presentation Controls: Interactive Serial Commands (NORMAL, WASTE, etc.)
 * ============================================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ============================================================================
// HARDWARE PIN DEFINITIONS
// ============================================================================

// Sensors
#define PIN_DHT            15    // DHT22 Data Pin
#define DHT_TYPE           DHT22
#define PIN_PIR            13    // PIR Motion Sensor (Digital Input)
#define PIN_LDR            34    // LDR Analog Output (ADC1 Channel 6)

// I2C OLED Display
#define SCREEN_WIDTH       128
#define SCREEN_HEIGHT      64
#define OLED_RESET         -1
#define OLED_I2C_ADDR      0x3C

// Appliance Push Buttons (Active LOW with internal INPUT_PULLUP)
#define PIN_BTN_AC         32
#define PIN_BTN_FAN        33
#define PIN_BTN_TV         25
#define PIN_BTN_LIGHT      26
#define PIN_BTN_FRIDGE     27
#define PIN_BTN_HEATER     14
#define PIN_BTN_MICRO      12

// Appliance State LEDs (Active HIGH)
#define PIN_LED_AC         23    // Red LED
#define PIN_LED_FAN        19    // Blue LED
#define PIN_LED_TV         18    // Cyan LED
#define PIN_LED_LIGHT       5    // Yellow LED
#define PIN_LED_FRIDGE     17    // Green LED (TX2)
#define PIN_LED_HEATER     16    // Red LED (RX2)
#define PIN_LED_MICRO       4    // Magenta/Amber LED

// ============================================================================
// SYSTEM & NETWORK CONFIGURATION
// ============================================================================

// WiFi Configuration (Wokwi Virtual WiFi)
const char* WIFI_SSID           = "Wokwi-GUEST";
const char* WIFI_PASS           = "";

// MQTT Broker Configuration
const char* MQTT_BROKER         = "broker.hivemq.com";
const uint16_t MQTT_PORT        = 1883;
const char* TOPIC_TELEMETRY     = "smart_home/telemetry";
const char* TOPIC_SENSORS       = "smart_home/sensors";
const char* TOPIC_APPLIANCES    = "smart_home/appliances";
const char* TOPIC_ENERGY        = "smart_home/energy";
const char* TOPIC_CONTROL       = "smart_home/control";

// Thresholds & Operational Intervals
const uint32_t TELEMETRY_INTERVAL_MS = 2500;  // Publish every 2.5 seconds
const uint32_t OLED_CYCLE_INTERVAL_MS= 3000;  // Switch OLED page every 3 seconds
const uint32_t MQTT_RETRY_INTERVAL_MS= 5000;  // Reconnect retry every 5 seconds
const uint16_t HIGH_LOAD_THRESHOLD_W = 3000;  // Alert when total load >= 3000 W
const uint16_t DARK_LUX_THRESHOLD    = 300;   // Lux threshold for room brightness

// ============================================================================
// APPLIANCE DATA MODEL
// ============================================================================

struct Appliance {
  const char* name;          // User-friendly display name
  const char* key;           // JSON key identifier
  uint8_t btnPin;            // Button input pin
  uint8_t ledPin;            // LED output pin
  uint16_t ratedPowerW;      // Rated power consumption in Watts
  bool state;                // Current state (true = ON, false = OFF)
  int lastReading;           // Raw reading for debouncing
  int buttonState;           // Debounced button state
  unsigned long lastDebounce;// Debounce timestamp
};

// Appliance Initial Configuration Table
// Easy to modify power ratings from this single location:
Appliance appliances[] = {
  {"Air Conditioner", "ac",          PIN_BTN_AC,     PIN_LED_AC,     1500, false, HIGH, HIGH, 0},
  {"Ceiling Fan",     "fan",         PIN_BTN_FAN,    PIN_LED_FAN,      75, false, HIGH, HIGH, 0},
  {"Television",      "tv",          PIN_BTN_TV,     PIN_LED_TV,      120, false, HIGH, HIGH, 0},
  {"Room Light",      "room_light",  PIN_BTN_LIGHT,  PIN_LED_LIGHT,    20, false, HIGH, HIGH, 0},
  {"Refrigerator",    "refrigerator",PIN_BTN_FRIDGE, PIN_LED_FRIDGE,  150, true,  HIGH, HIGH, 0}, // Refrigerator ON by default
  {"Space Heater",    "heater",      PIN_BTN_HEATER, PIN_LED_HEATER, 2000, false, HIGH, HIGH, 0},
  {"Microwave",       "microwave",   PIN_BTN_MICRO,  PIN_LED_MICRO,  1000, false, HIGH, HIGH, 0}
};

const uint8_t NUM_APPLIANCES = sizeof(appliances) / sizeof(appliances[0]);

// ============================================================================
// GLOBAL STATE VARIABLES
// ============================================================================

DHT dht(PIN_DHT, DHT_TYPE);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// Environmental & State Variables
float currentTemp       = 24.0;
float currentHumidity   = 45.0;
int currentOccupancy    = 0;
int rawLdrValue         = 0;
int lightLevelLux       = 0;
uint32_t totalPowerW    = 0;
float cumulativeEnergyKWh = 0.0;

// Smart Home Logic Flags
bool wasteFlag          = false;
bool highLoadFlag       = false;
String wasteReason      = "Normal";

// Manual overrides for serial presentation testing
bool manualOccupancyOverride = false;
int manualOccupancyVal       = 0;

// Timers
unsigned long lastTelemetryTime      = 0;
unsigned long lastOledCycleTime      = 0;
unsigned long lastMqttRetryTime      = 0;
unsigned long lastEnergyCalcTime     = 0;
uint8_t currentOledPage              = 0;

// ============================================================================
// FORWARD DECLARATIONS
// ============================================================================
void setupHardware();
void setupNetworking();
void readSensors();
void updateAppliances();
void calculatePower();
void checkWasteConditions();
void updateDisplay();
void handleMQTT();
void publishTelemetry();
void handleSerialCommands();
void applyPreset(const String& presetName);
void printSerialDashboard();
void mqttCallback(char* topic, byte* payload, unsigned int length);

// ============================================================================
// ARDUINO SETUP
// ============================================================================
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n========================================================");
  Serial.println("  AI FOR IOT CAPSTONE - SMART HOME SIMULATOR (PHASE 1) ");
  Serial.println("========================================================");

  setupHardware();
  setupNetworking();
  calculatePower();
  checkWasteConditions();

  Serial.println("\n[SYSTEM] Initialization complete. Virtual Home ready.");
  Serial.println("[HELP] Type 'HELP' in Serial Monitor to view demo commands.");
  Serial.println("========================================================\n");
}

// ============================================================================
// MAIN LOOP
// ============================================================================
void loop() {
  // 1. Process Physical Appliance Controls & Debouncing
  updateAppliances();

  // 2. Handle Non-blocking MQTT Connectivity & Incoming Messages
  handleMQTT();

  // 3. Process Interactive Serial Monitor Demo Commands
  handleSerialCommands();

  unsigned long currentMillis = millis();

  // 4. Periodic Sensor Sampling & Telemetry Publishing (Every 2.5s)
  if (currentMillis - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryTime = currentMillis;
    readSensors();
    calculatePower();
    checkWasteConditions();
    publishTelemetry();
    printSerialDashboard();
  }

  // 5. Periodic OLED Page Switching (Every 3s)
  if (currentMillis - lastOledCycleTime >= OLED_CYCLE_INTERVAL_MS) {
    lastOledCycleTime = currentMillis;
    currentOledPage = (currentOledPage + 1) % 2;
    updateDisplay();
  }
}

// ============================================================================
// HARDWARE INITIALIZATION
// ============================================================================
void setupHardware() {
  Serial.println("[INIT] Initializing hardware peripherals...");

  // Initialize Sensors
  pinMode(PIN_PIR, INPUT);
  pinMode(PIN_LDR, INPUT);
  dht.begin();

  // Initialize Appliance Buttons and LEDs
  for (uint8_t i = 0; i < NUM_APPLIANCES; i++) {
    pinMode(appliances[i].btnPin, INPUT_PULLUP);
    pinMode(appliances[i].ledPin, OUTPUT);
    digitalWrite(appliances[i].ledPin, appliances[i].state ? HIGH : LOW);
  }

  // Initialize I2C OLED Display
  Wire.begin(21, 22);
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDR)) {
    Serial.println("[WARN] SSD1306 OLED initialization failed or not attached.");
  } else {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(10, 10);
    display.println("Smart Home IoT");
    display.setCursor(10, 26);
    display.println("Energy Simulator");
    display.setCursor(10, 42);
    display.println("Phase 1 Starting...");
    display.display();
    delay(1000);
  }

  lastEnergyCalcTime = millis();
  Serial.println("[INIT] Peripherals and pins configured.");
}

// ============================================================================
// NETWORKING & MQTT SETUP
// ============================================================================
void setupNetworking() {
  Serial.print("[WIFI] Connecting to SSID: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 8000) {
    delay(200);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Connected! IP Address: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n[WIFI] Warning: Virtual WiFi not connected. Simulator will continue locally.");
  }

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setBufferSize(768); // Sufficient buffer for JSON telemetry
}

// ============================================================================
// SENSOR ACQUISITION
// ============================================================================
void readSensors() {
  // Read DHT22
  float t = dht.readTemperature();
  float h = dht.readHumidity();

  if (!isnan(t) && !isnan(h)) {
    currentTemp = t;
    currentHumidity = h;
  }

  // Read PIR Motion Sensor (or use manual override if requested via Serial)
  if (manualOccupancyOverride) {
    currentOccupancy = manualOccupancyVal;
  } else {
    currentOccupancy = digitalRead(PIN_PIR) == HIGH ? 1 : 0;
  }

  // Read LDR Photoresistor (ESP32 ADC is 12-bit: 0 - 4095)
  rawLdrValue = analogRead(PIN_LDR);
  // Map raw ADC to an approximate simulated ambient Lux level (0 to 1000 Lux)
  lightLevelLux = map(rawLdrValue, 0, 4095, 10, 1000);
  if (lightLevelLux < 0) lightLevelLux = 0;
}

// ============================================================================
// APPLIANCE CONTROL & DEBOUNCING
// ============================================================================
void updateAppliances() {
  unsigned long now = millis();

  for (uint8_t i = 0; i < NUM_APPLIANCES; i++) {
    int reading = digitalRead(appliances[i].btnPin);

    // If reading changed due to noise or pressing
    if (reading != appliances[i].lastReading) {
      appliances[i].lastDebounce = now;
    }

    // Debounce period: 50 ms
    if ((now - appliances[i].lastDebounce) > 50) {
      if (reading != appliances[i].buttonState) {
        appliances[i].buttonState = reading;

        // Button pressed (Active LOW)
        if (appliances[i].buttonState == LOW) {
          appliances[i].state = !appliances[i].state;
          Serial.print("[APPLIANCE] Toggled ");
          Serial.print(appliances[i].name);
          Serial.print(" -> ");
          Serial.println(appliances[i].state ? "ON" : "OFF");

          calculatePower();
          checkWasteConditions();
          updateDisplay();
        }
      }
    }

    appliances[i].lastReading = reading;

    // Drive physical LED output
    digitalWrite(appliances[i].ledPin, appliances[i].state ? HIGH : LOW);
  }
}

// ============================================================================
// ELECTRICAL POWER CALCULATION (DETERMINISTIC)
// ============================================================================
void calculatePower() {
  uint32_t activeSum = 0;
  for (uint8_t i = 0; i < NUM_APPLIANCES; i++) {
    if (appliances[i].state) {
      activeSum += appliances[i].ratedPowerW;
    }
  }
  totalPowerW = activeSum;

  // Integrate cumulative electrical energy in kWh
  unsigned long now = millis();
  if (lastEnergyCalcTime > 0) {
    float deltaHours = (float)(now - lastEnergyCalcTime) / 3600000.0f;
    cumulativeEnergyKWh += (totalPowerW * deltaHours) / 1000.0f;
  }
  lastEnergyCalcTime = now;
}

// ============================================================================
// SMART HOME LOGIC RULES (PRE-ML BASELINE RULES)
// ============================================================================
void checkWasteConditions() {
  wasteFlag = false;
  highLoadFlag = false;
  wasteReason = "Normal Operation";

  bool acState      = appliances[0].state;
  bool fanState     = appliances[1].state;
  bool tvState      = appliances[2].state;
  bool lightState   = appliances[3].state;
  bool heaterState  = appliances[5].state;
  bool microState   = appliances[6].state;

  // Rule 1: Vacancy Waste Detection (Occupancy = 0 while appliances remain ON)
  if (currentOccupancy == 0) {
    if (acState && tvState && lightState) {
      wasteFlag = true;
      wasteReason = "Waste: AC, TV & Light ON with room vacant";
    } else if (acState) {
      wasteFlag = true;
      wasteReason = "Waste: AC cooling unoccupied room";
    } else if (heaterState) {
      wasteFlag = true;
      wasteReason = "Waste: Space heater running in empty room";
    } else if (tvState) {
      wasteFlag = true;
      wasteReason = "Waste: TV left powered ON in vacant room";
    } else if (lightState) {
      wasteFlag = true;
      wasteReason = "Waste: Room light burning in unoccupied room";
    } else if (fanState && !acState) {
      wasteFlag = true;
      wasteReason = "Waste: Fan spinning in vacant room";
    }
  }

  // Rule 2: Daylight Lighting Waste (Light ON when ambient light is abundant)
  if (lightState && lightLevelLux > DARK_LUX_THRESHOLD) {
    wasteFlag = true;
    if (currentOccupancy == 0) {
      wasteReason = "Waste: Light ON during broad daylight (room empty)";
    } else {
      wasteReason = "Waste: Room light ON during ample daylight";
    }
  }

  // Rule 3: High Load / Overload Alert
  uint8_t heavyLoadCount = 0;
  if (acState) heavyLoadCount++;
  if (heaterState) heavyLoadCount++;
  if (microState) heavyLoadCount++;

  if (totalPowerW >= HIGH_LOAD_THRESHOLD_W || heavyLoadCount >= 2) {
    highLoadFlag = true;
    if (heavyLoadCount >= 2) {
      wasteReason = "High Load: Multiple heavy appliances active concurrently";
    } else {
      wasteReason = "High Load: Household power exceeds 3000 W limit";
    }
  }
}

// ============================================================================
// OLED DISPLAY RENDERING (CYCLING PAGES)
// ============================================================================
void updateDisplay() {
  display.clearDisplay();

  if (currentOledPage == 0) {
    // PAGE 0: Telemetry Overview & Energy
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.print("SMART HOME MONITOR");
    display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

    display.setCursor(0, 13);
    display.print("Temp: ");
    display.print(currentTemp, 1);
    display.print(" C");

    display.setCursor(68, 13);
    display.print("Hum: ");
    display.print(currentHumidity, 0);
    display.print("%");

    display.setCursor(0, 24);
    display.print("Occupancy: ");
    display.print(currentOccupancy ? "YES" : "NO");

    display.setCursor(0, 35);
    display.print("Light: ");
    display.print(lightLevelLux);
    display.print(" lux");

    // Total Power Banner
    display.setCursor(0, 46);
    display.print("Power: ");
    display.setTextSize(1);
    display.print(totalPowerW);
    display.print(" W");

    // Status / Alert Notification Line
    display.setCursor(0, 56);
    if (highLoadFlag) {
      display.print("! HIGH LOAD ALERT !");
    } else if (wasteFlag) {
      display.print("! WASTEFUL USAGE !");
    } else {
      display.print("Status: Normal [OK]");
    }

  } else {
    // PAGE 1: Individual Appliance Matrix
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.print("APPLIANCE MATRIX");
    display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

    // Row 1
    display.setCursor(0, 13);
    display.print("AC :");
    display.print(appliances[0].state ? "ON " : "OFF");
    display.setCursor(64, 13);
    display.print("FAN:");
    display.print(appliances[1].state ? "ON" : "OFF");

    // Row 2
    display.setCursor(0, 24);
    display.print("TV :");
    display.print(appliances[2].state ? "ON " : "OFF");
    display.setCursor(64, 24);
    display.print("LIT:");
    display.print(appliances[3].state ? "ON" : "OFF");

    // Row 3
    display.setCursor(0, 35);
    display.print("REF:");
    display.print(appliances[4].state ? "ON " : "OFF");
    display.setCursor(64, 35);
    display.print("HTR:");
    display.print(appliances[5].state ? "ON" : "OFF");

    // Row 4
    display.setCursor(0, 46);
    display.print("MIC:");
    display.print(appliances[6].state ? "ON " : "OFF");
    display.setCursor(64, 46);
    display.print("LOAD: ");
    display.print(totalPowerW);
    display.print("W");

    // Energy tally
    display.setCursor(0, 56);
    display.print("Energy: ");
    display.print(cumulativeEnergyKWh, 3);
    display.print(" kWh");
  }

  display.display();
}

// ============================================================================
// MQTT MANAGEMENT (RESILIENT & NON-BLOCKING)
// ============================================================================
void handleMQTT() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  if (!mqttClient.connected()) {
    unsigned long now = millis();
    if (now - lastMqttRetryTime >= MQTT_RETRY_INTERVAL_MS) {
      lastMqttRetryTime = now;
      Serial.print("[MQTT] Connecting to broker ");
      Serial.print(MQTT_BROKER);
      Serial.print("...");

      String clientId = "SmartHome-ESP32-" + String((uint32_t)ESP.getEfuseMac(), HEX);

      if (mqttClient.connect(clientId.c_str())) {
        Serial.println(" CONNECTED!");
        mqttClient.subscribe(TOPIC_CONTROL);
        mqttClient.publish("smart_home/status", "{\"status\":\"online\"}");
      } else {
        Serial.print(" Failed (rc=");
        Serial.print(mqttClient.state());
        Serial.println("). Non-blocking retry in 5s. Simulator running locally.");
      }
    }
  } else {
    mqttClient.loop();
  }
}

// ============================================================================
// TELEMETRY PUBLISHING (JSON ENCODED)
// ============================================================================
void publishTelemetry() {
  // Construct Comprehensive Combined JSON Payload
  StaticJsonDocument<512> doc;

  doc["uptime_ms"]    = millis();
  doc["temperature"]  = serialized(String(currentTemp, 1));
  doc["humidity"]     = serialized(String(currentHumidity, 1));
  doc["occupancy"]    = currentOccupancy;
  doc["light_level"]  = lightLevelLux;

  // Individual Appliance States (0 or 1)
  doc["ac"]           = appliances[0].state ? 1 : 0;
  doc["fan"]          = appliances[1].state ? 1 : 0;
  doc["tv"]           = appliances[2].state ? 1 : 0;
  doc["room_light"]   = appliances[3].state ? 1 : 0;
  doc["refrigerator"] = appliances[4].state ? 1 : 0;
  doc["heater"]       = appliances[5].state ? 1 : 0;
  doc["microwave"]    = appliances[6].state ? 1 : 0;

  // Electrical Power & Logic Flags
  doc["power_w"]       = totalPowerW;
  doc["energy_kwh"]    = serialized(String(cumulativeEnergyKWh, 4));
  doc["waste_flag"]    = wasteFlag ? 1 : 0;
  doc["high_load_flag"]= highLoadFlag ? 1 : 0;
  doc["status_msg"]    = wasteReason;

  char jsonBuffer[512];
  serializeJson(doc, jsonBuffer);

  // Publish to Primary Telemetry Topic if MQTT is Connected
  if (mqttClient.connected()) {
    mqttClient.publish(TOPIC_TELEMETRY, jsonBuffer);

    // Also publish to modular topics for decoupled subscribers
    StaticJsonDocument<128> docSensors;
    docSensors["temperature"] = serialized(String(currentTemp, 1));
    docSensors["humidity"]    = serialized(String(currentHumidity, 1));
    docSensors["occupancy"]   = currentOccupancy;
    docSensors["light_level"] = lightLevelLux;
    char bufferSensors[128];
    serializeJson(docSensors, bufferSensors);
    mqttClient.publish(TOPIC_SENSORS, bufferSensors);

    StaticJsonDocument<128> docEnergy;
    docEnergy["power_w"]        = totalPowerW;
    docEnergy["energy_kwh"]     = serialized(String(cumulativeEnergyKWh, 4));
    docEnergy["waste_flag"]     = wasteFlag ? 1 : 0;
    docEnergy["high_load_flag"] = highLoadFlag ? 1 : 0;
    char bufferEnergy[128];
    serializeJson(docEnergy, bufferEnergy);
    mqttClient.publish(TOPIC_ENERGY, bufferEnergy);

    Serial.println("[MQTT] Telemetry published to " + String(TOPIC_TELEMETRY));
  } else {
    Serial.println("[LOCAL] Telemetry generated (MQTT not connected)");
  }
}

// ============================================================================
// SERIAL MONITOR TELEMETRY LOG
// ============================================================================
void printSerialDashboard() {
  Serial.println("--------------------------------------------------------");
  Serial.printf("Env Sensors: Temp: %.1f C | Humidity: %.1f %% | Light: %d lux\n",
                currentTemp, currentHumidity, lightLevelLux);
  Serial.printf("Occupancy  : %s\n", currentOccupancy ? "YES (Occupied)" : "NO (Vacant)");
  Serial.println("Appliances :");
  for (uint8_t i = 0; i < NUM_APPLIANCES; i++) {
    Serial.printf("  - %-16s [%-12s]: %s (%4d W)\n",
                  appliances[i].name, appliances[i].key,
                  appliances[i].state ? "ON " : "OFF",
                  appliances[i].state ? appliances[i].ratedPowerW : 0);
  }
  Serial.printf("TOTAL POWER: %4d W | CUMULATIVE ENERGY: %.4f kWh\n",
                totalPowerW, cumulativeEnergyKWh);
  Serial.printf("FLAGS      : Waste=%d | HighLoad=%d | Note: %s\n",
                wasteFlag, highLoadFlag, wasteReason.c_str());
  Serial.printf("CONNECT    : WiFi=%s | MQTT=%s\n",
                WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected",
                mqttClient.connected() ? "Connected" : "Disconnected");
  Serial.println("--------------------------------------------------------");
}

// ============================================================================
// DEMO PRESETS & PRESENTATION MODES
// ============================================================================
void applyPreset(const String& presetName) {
  String cmd = presetName;
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "NORMAL") {
    // Normal household: Occupant present, Light, Fan and Fridge active
    manualOccupancyOverride = true;
    manualOccupancyVal = 1;
    appliances[0].state = false; // AC OFF
    appliances[1].state = true;  // Fan ON
    appliances[2].state = false; // TV OFF
    appliances[3].state = true;  // Light ON
    appliances[4].state = true;  // Fridge ON
    appliances[5].state = false; // Heater OFF
    appliances[6].state = false; // Microwave OFF
    Serial.println("\n>>> [PRESET APPLIED] NORMAL MODE (Occupant Present, Fan+Light+Fridge)");

  } else if (cmd == "WASTE" || cmd == "WASTEFUL") {
    // Wasteful scenario: Room vacant, but AC, TV and Room Light left running!
    manualOccupancyOverride = true;
    manualOccupancyVal = 0;
    appliances[0].state = true;  // AC ON (1500W)
    appliances[1].state = false; // Fan OFF
    appliances[2].state = true;  // TV ON (120W)
    appliances[3].state = true;  // Light ON (20W)
    appliances[4].state = true;  // Fridge ON (150W)
    appliances[5].state = false; // Heater OFF
    appliances[6].state = false; // Microwave OFF
    Serial.println("\n>>> [PRESET APPLIED] WASTEFUL USAGE (Room Empty, AC+TV+Light ON)");

  } else if (cmd == "HIGH_LOAD" || cmd == "HIGH LOAD") {
    // High load scenario: Multiple heating/cooling loads simultaneously active
    manualOccupancyOverride = true;
    manualOccupancyVal = 1;
    appliances[0].state = true;  // AC ON (1500W)
    appliances[1].state = true;  // Fan ON (75W)
    appliances[2].state = false; // TV OFF
    appliances[3].state = true;  // Light ON (20W)
    appliances[4].state = true;  // Fridge ON (150W)
    appliances[5].state = true;  // Heater ON (2000W)
    appliances[6].state = true;  // Microwave ON (1000W)
    Serial.println("\n>>> [PRESET APPLIED] HIGH LOAD MODE (AC + Heater + Microwave Active = 4745W)");

  } else if (cmd == "SPIKE") {
    // Instantaneous load spike: Toggle Space Heater (2000W) or Microwave
    appliances[5].state = !appliances[5].state;
    Serial.printf("\n>>> [PRESET APPLIED] SPIKE EVENT! Space Heater is now %s\n",
                  appliances[5].state ? "ON (+2000W SPIKE)" : "OFF");

  } else if (cmd == "RESET" || cmd == "ALL_OFF") {
    // Baseline state: Only refrigerator base load ON
    manualOccupancyOverride = false;
    for (uint8_t i = 0; i < NUM_APPLIANCES; i++) {
      appliances[i].state = (i == 4); // Only fridge stays true
    }
    Serial.println("\n>>> [PRESET APPLIED] RESET (Baseline Load: Refrigerator ON)");

  } else if (cmd == "ALL_ON") {
    // Peak stress test: Everything ON
    for (uint8_t i = 0; i < NUM_APPLIANCES; i++) {
      appliances[i].state = true;
    }
    Serial.println("\n>>> [PRESET APPLIED] ALL APPLIANCES ON (Peak Household Load)");

  } else {
    Serial.println("[PRESET] Unknown preset: " + cmd);
    return;
  }

  // Update physical LED pins immediately
  for (uint8_t i = 0; i < NUM_APPLIANCES; i++) {
    digitalWrite(appliances[i].ledPin, appliances[i].state ? HIGH : LOW);
  }

  calculatePower();
  checkWasteConditions();
  updateDisplay();
  publishTelemetry();
  printSerialDashboard();
}

// ============================================================================
// SERIAL COMMAND INTERFACE
// ============================================================================
void handleSerialCommands() {
  if (!Serial.available()) return;

  String input = Serial.readStringUntil('\n');
  input.trim();
  if (input.length() == 0) return;

  String upper = input;
  upper.toUpperCase();

  if (upper == "HELP") {
    Serial.println("\n========================================================");
    Serial.println("           SMART HOME SIMULATOR DEMO COMMANDS           ");
    Serial.println("========================================================");
    Serial.println("  NORMAL       : Normal household (Occupied, 245W, No Waste)");
    Serial.println("  WASTE        : Vacant room with AC+TV+Light ON (1790W)");
    Serial.println("  HIGH_LOAD    : Multiple heavy loads ON simultaneously (>4000W)");
    Serial.println("  SPIKE        : Trigger immediate 2000W Space Heater spike");
    Serial.println("  RESET        : Reset all appliances except Refrigerator");
    Serial.println("  ALL_ON       : Turn every appliance ON");
    Serial.println("  OCC 1 / OCC 0: Override occupancy sensor state");
    Serial.println("  OCC AUTO     : Revert to real-time PIR sensor reading");
    Serial.println("  TOGGLE <ID>  : Toggle appliance (ac, fan, tv, light, fridge, heater, micro)");
    Serial.println("  STATUS       : Print immediate telemetry snapshot");
    Serial.println("========================================================\n");

  } else if (upper == "STATUS") {
    readSensors();
    calculatePower();
    checkWasteConditions();
    printSerialDashboard();

  } else if (upper.startsWith("OCC ")) {
    String arg = upper.substring(4);
    arg.trim();
    if (arg == "AUTO") {
      manualOccupancyOverride = false;
      Serial.println("[OCC] Reverted to physical PIR sensor input.");
    } else {
      manualOccupancyOverride = true;
      manualOccupancyVal = arg.toInt() ? 1 : 0;
      Serial.printf("[OCC] Manual occupancy override set to: %d\n", manualOccupancyVal);
    }
    readSensors();
    checkWasteConditions();
    updateDisplay();

  } else if (upper.startsWith("TOGGLE ")) {
    String target = upper.substring(7);
    target.trim();
    bool found = false;
    for (uint8_t i = 0; i < NUM_APPLIANCES; i++) {
      String keyStr = String(appliances[i].key);
      keyStr.toUpperCase();
      if (keyStr == target || String(i + 1) == target) {
        appliances[i].state = !appliances[i].state;
        digitalWrite(appliances[i].ledPin, appliances[i].state ? HIGH : LOW);
        Serial.printf("[TOGGLE] %s is now %s (%d W)\n",
                      appliances[i].name, appliances[i].state ? "ON" : "OFF",
                      appliances[i].state ? appliances[i].ratedPowerW : 0);
        found = true;
        break;
      }
    }
    if (!found) {
      Serial.println("[TOGGLE] Unknown appliance: " + target);
    } else {
      calculatePower();
      checkWasteConditions();
      updateDisplay();
    }

  } else {
    // Treat as preset name
    applyPreset(input);
  }
}

// ============================================================================
// REMOTE MQTT CONTROL CALLBACK
// ============================================================================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  char msg[256];
  if (length >= sizeof(msg)) length = sizeof(msg) - 1;
  memcpy(msg, payload, length);
  msg[length] = '\0';

  Serial.printf("[MQTT RX] Topic: %s | Payload: %s\n", topic, msg);

  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, msg);
  if (!err) {
    if (doc.containsKey("preset")) {
      applyPreset(doc["preset"].as<String>());
    } else if (doc.containsKey("toggle")) {
      String appKey = doc["toggle"].as<String>();
      for (uint8_t i = 0; i < NUM_APPLIANCES; i++) {
        if (String(appliances[i].key) == appKey) {
          appliances[i].state = !appliances[i].state;
          digitalWrite(appliances[i].ledPin, appliances[i].state ? HIGH : LOW);
          calculatePower();
          checkWasteConditions();
          updateDisplay();
          publishTelemetry();
          break;
        }
      }
    }
  }
}
