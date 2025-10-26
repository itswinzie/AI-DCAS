#define BLYNK_MAX_SENDBYTES 256
#define BLYNK_PRINT Serial
#include <WiFi.h>
#include <WiFiClient.h>
#include <BlynkSimpleEsp32.h>
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

char auth[] = "-NKy-xV5x45tcyMAdwiGQiDeNOgdT0Xn";
char ssid[] = "POCO F7";
char pass[] = "qwertyuiop";
const char* blynkServer = "10.100.70.60"; // perlu ubah jika ip address berubah lagi!!!
const int blynkPort = 8080;

const int NRF_CE_PIN = 17;
const int NRF_CSN_PIN = 5;

const byte PIPE_ADDRESS[6] = "SIGNL";
const rf24_pa_dbm_e PA_LEVEL = RF24_PA_LOW;
const rf24_datarate_e DATA_RATE = RF24_250KBPS;
const byte CHANNEL = 76;
const uint8_t PAYLOAD_SIZE = 32;

const int RELAY_PIN = 13;
const bool RELAY_HIGH_UNTUK_ON = false;

const int IR_PIN = 15;
const int IR_DETECTED_STATE = LOW;

RF24 radio(NRF_CE_PIN, NRF_CSN_PIN);

bool currentRelayState = false;
bool irControlActive = false;
unsigned long irClearTime = 0;

WidgetLED led1(V1);
WidgetLED led2(V2);
WidgetTerminal terminal(V3);

void logAndTerminal(String message) {
  Serial.println(message);
  if (Blynk.connected()) {
    terminal.println(message);
    terminal.flush();
  }
}

void updateBlynkStatus() {
  if (Blynk.connected()) {
    if (currentRelayState) led1.on();
    else led1.off();

    if (irControlActive) led2.on();
    else led2.off();

    Blynk.virtualWrite(V0, currentRelayState ? 1 : 0);
  }
}

void setRelayState(bool state) {
  if (state != currentRelayState) {
    if (state) {
      digitalWrite(RELAY_PIN, RELAY_HIGH_UNTUK_ON ? HIGH : LOW);
      currentRelayState = true;
      logAndTerminal("[RELAY] Dihidupkan (Pintu Dibuka).");
      if (Blynk.connected()) {
        delay(100);
        //Blynk.notify("Pintu Dibuka");
      }
    } else {
      digitalWrite(RELAY_PIN, RELAY_HIGH_UNTUK_ON ? LOW : HIGH);
      currentRelayState = false;
      logAndTerminal("[RELAY] Dimatikan (Pintu Dikunci).");
      if (Blynk.connected()) {
        delay(100);
        //Blynk.notify("Pintu Dikunci");
      }
    }
    updateBlynkStatus();
  }
}

void handleNRFMessage(const char* msg) {
  logAndTerminal(String("[NRF] Mesej diterima: ") + msg);
  if (msg[0] == '\0') {
    logAndTerminal("[NRF ERROR] Mesej yang diterima kosong atau tidak sah.");
    return;
  }

  if (strcmp(msg, "RELAY_ON") == 0) {
    setRelayState(true);
    irControlActive = true;
    irClearTime = 0;
    logAndTerminal("[NRF] IR Control Diaktifkan.");
    if (Blynk.connected()) led2.on();

  } else if (strcmp(msg, "RELAY_OFF") == 0) {
    setRelayState(false);
    irControlActive = false;
    irClearTime = 0;
    logAndTerminal("[NRF] IR Control Dinonaktifkan.");
    if (Blynk.connected()) led2.off();

  } else {
    logAndTerminal("[NRF] Mesej tidak dikenali: '" + String(msg) + "'");
  }
}

BLYNK_CONNECTED() {
  logAndTerminal("[BLYNK] Terhubung ke server lokal.");
  terminal.println("----------------------");
  terminal.println(">>> SISTEM AIDCAS <<<");
  terminal.println("----------------------");
  terminal.flush();
  Blynk.syncVirtual(V0);
  updateBlynkStatus();
}

BLYNK_WRITE(V0) {
  int pinValue = param.asInt();
  if (!irControlActive) {
    setRelayState(pinValue == 1);
  } else {
    logAndTerminal("[BLYNK] Kawalan manual diabaikan: IR control aktif.");
    Blynk.virtualWrite(V0, currentRelayState ? 1 : 0);
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Memulakan Sistem AI-DCAS (ESP32) ===");

  pinMode(RELAY_PIN, OUTPUT);
  pinMode(IR_PIN, INPUT);
  setRelayState(false);

  SPI.begin(18, 19, 23, NRF_CSN_PIN);
  logAndTerminal("[SETUP] SPI telah dimulakan.");

  if (!radio.begin()) {
    logAndTerminal("[NRF ERROR] NRF24L01 gagal dikesan!");
    while (1) {
      delay(100);
      Serial.print(".");
    }
  } else {
    logAndTerminal("[NRF] Modul NRF24L01 dikesan.");
    radio.setPALevel(PA_LEVEL);
    radio.setDataRate(DATA_RATE);
    radio.setChannel(CHANNEL);
    radio.openReadingPipe(1, PIPE_ADDRESS);
    radio.startListening();
    radio.setPayloadSize(PAYLOAD_SIZE);
    delay(100);
    logAndTerminal("[NRF] Siap menerima mesej pada paip 1.");
    radio.printDetails();
  }

  logAndTerminal("[BLYNK] Menghubungkan ke server lokal...");
  Blynk.begin(auth, ssid, pass, blynkServer, blynkPort);
}

void loop() {
  Blynk.run();

  if (radio.available()) {
    char msg[PAYLOAD_SIZE + 1] = "";
    radio.read(&msg, PAYLOAD_SIZE);
    msg[PAYLOAD_SIZE] = '\0';
    handleNRFMessage(msg);
  }

  if (irControlActive && currentRelayState) {
    int irState = digitalRead(IR_PIN);
    if (irState == IR_DETECTED_STATE) {
      irClearTime = 0;
    } else {
      if (irClearTime == 0) {
        irClearTime = millis();
        logAndTerminal("[IR] Objek tidak terdeteksi. Memulai timer...");
      } else if (millis() - irClearTime >= 2000) {
        logAndTerminal("[IR] Objek tidak terdeteksi selama 2s. Mematikan relay.");
        setRelayState(false);
        irControlActive = false;
        irClearTime = 0;
      }
    }
  }
}
