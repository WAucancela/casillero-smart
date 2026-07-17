// ══════════════════════════════════════════════════════════════
//  Firmware controlador de casilleros — ESP32
//  Sistema de Casilleros Automatizados
//
//  Protocolo MQTT (contrato con backend/infrastructure/hardware):
//    Suscribe:  casilleros/{CONTROLADOR_ID}/puerto/{N}/abrir
//               casilleros/{CONTROLADOR_ID}/puerto/{N}/bloquear
//               casilleros/{CONTROLADOR_ID}/puerto/{N}/estado
//    Publica:   casilleros/respuesta/{CONTROLADOR_ID}/puerto/{N}
//               casilleros/respuesta/{CONTROLADOR_ID}/ping
//
//  Payload de comando (JSON):
//    {"accion":"abrir","casillero_numero":"A-101","duracion_segundos":5}
//
//  Librerías (Library Manager de Arduino IDE):
//    - PubSubClient (Nick O'Leary)  >= 2.8
//    - ArduinoJson (Benoit Blanchon) >= 7.x
// ══════════════════════════════════════════════════════════════

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

// Estado por puerto (índice 0 = puerto 1)
unsigned long releApagaEn[NUM_PUERTOS] = {0};  // millis() en que debe cerrarse el relé (0 = inactivo)
bool puertoBloqueado[NUM_PUERTOS] = {false};   // bloqueado: ignora comandos de apertura

unsigned long ultimoPing = 0;
unsigned long ultimoIntentoMqtt = 0;

// ── Helpers de hardware ──────────────────────────────────────

void releEscribir(int idx, bool activar) {
  bool nivel = RELE_ACTIVO_BAJO ? !activar : activar;
  digitalWrite(PIN_RELE[idx], nivel ? HIGH : LOW);
}

// Lee el sensor de puerta; sin sensores se asume cerrado
const char* estadoPuerta(int idx) {
  if (!USAR_SENSORES) return "desconocido";
  // Reed switch a GND con pull-up: LOW = puerta cerrada (imán presente)
  return digitalRead(PIN_SENSOR[idx]) == LOW ? "cerrado" : "abierto";
}

// ── Publicación de respuestas ────────────────────────────────

void publicarRespuesta(int puerto, const char* accion, bool ok, const char* detalle) {
  char topic[80];
  snprintf(topic, sizeof(topic), "casilleros/respuesta/%s/puerto/%d", CONTROLADOR_ID, puerto);

  JsonDocument doc;
  doc["controlador_id"] = CONTROLADOR_ID;
  doc["puerto"] = puerto;
  doc["accion"] = accion;
  doc["ok"] = ok;
  doc["detalle"] = detalle;
  doc["puerta"] = estadoPuerta(puerto - 1);
  doc["bloqueado"] = puertoBloqueado[puerto - 1];

  char payload[256];
  serializeJson(doc, payload, sizeof(payload));
  mqtt.publish(topic, payload, false);
  Serial.printf("[MQTT] → %s %s\n", topic, payload);
}

void publicarPing() {
  char topic[80];
  snprintf(topic, sizeof(topic), "casilleros/respuesta/%s/ping", CONTROLADOR_ID);

  JsonDocument doc;
  doc["controlador_id"] = CONTROLADOR_ID;
  doc["ip"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["uptime_s"] = millis() / 1000;

  char payload[192];
  serializeJson(doc, payload, sizeof(payload));
  mqtt.publish(topic, payload, false);
}

// ── Acciones ──────────────────────────────────────────────────

void accionAbrir(int puerto, int duracionSegundos) {
  int idx = puerto - 1;
  if (puertoBloqueado[idx]) {
    publicarRespuesta(puerto, "abrir", false, "puerto bloqueado");
    return;
  }
  releEscribir(idx, true);
  releApagaEn[idx] = millis() + (unsigned long)duracionSegundos * 1000UL;
  Serial.printf("[RELE] Puerto %d abierto por %d s\n", puerto, duracionSegundos);
  publicarRespuesta(puerto, "abrir", true, "cerradura activada");
}

void accionBloquear(int puerto) {
  int idx = puerto - 1;
  puertoBloqueado[idx] = true;
  releEscribir(idx, false);
  releApagaEn[idx] = 0;
  publicarRespuesta(puerto, "bloquear", true, "puerto bloqueado");
}

void accionDesbloquear(int puerto) {
  puertoBloqueado[puerto - 1] = false;
  publicarRespuesta(puerto, "desbloquear", true, "puerto desbloqueado");
}

void accionEstado(int puerto) {
  publicarRespuesta(puerto, "estado", true, "consulta de estado");
}

// ── MQTT ──────────────────────────────────────────────────────

void onMensaje(char* topic, byte* payload, unsigned int length) {
  Serial.printf("[MQTT] ← %s\n", topic);

  // Extraer puerto y comando de: casilleros/{ID}/puerto/{N}/{cmd}
  int puerto = 0;
  char cmd[16] = {0};
  char patron[80];
  snprintf(patron, sizeof(patron), "casilleros/%s/puerto/%%d/%%15s", CONTROLADOR_ID);
  if (sscanf(topic, patron, &puerto, cmd) != 2) return;
  if (puerto < 1 || puerto > NUM_PUERTOS) {
    publicarRespuesta(puerto, cmd, false, "puerto fuera de rango");
    return;
  }

  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    publicarRespuesta(puerto, cmd, false, "payload JSON invalido");
    return;
  }

  const char* accion = doc["accion"] | cmd;

  if (strcmp(cmd, "abrir") == 0) {
    int duracion = doc["duracion_segundos"] | APERTURA_DEFAULT_S;
    accionAbrir(puerto, duracion);
  } else if (strcmp(cmd, "bloquear") == 0) {
    // El mismo topic acepta desbloquear (extensión futura del backend)
    if (strcmp(accion, "desbloquear") == 0) accionDesbloquear(puerto);
    else accionBloquear(puerto);
  } else if (strcmp(cmd, "estado") == 0) {
    accionEstado(puerto);
  }
}

bool conectarMqtt() {
  char clientId[64];
  snprintf(clientId, sizeof(clientId), "esp32-%s", CONTROLADOR_ID);

  // Last Will: avisa al backend si el controlador se cae
  char willTopic[80];
  snprintf(willTopic, sizeof(willTopic), "casilleros/respuesta/%s/offline", CONTROLADOR_ID);

  if (!mqtt.connect(clientId, MQTT_USER, MQTT_PASSWORD, willTopic, 1, false, "{\"online\":false}")) {
    Serial.printf("[MQTT] Fallo de conexion, rc=%d\n", mqtt.state());
    return false;
  }

  char topic[80];
  snprintf(topic, sizeof(topic), "casilleros/%s/puerto/+/abrir", CONTROLADOR_ID);
  mqtt.subscribe(topic, 1);
  snprintf(topic, sizeof(topic), "casilleros/%s/puerto/+/bloquear", CONTROLADOR_ID);
  mqtt.subscribe(topic, 1);
  snprintf(topic, sizeof(topic), "casilleros/%s/puerto/+/estado", CONTROLADOR_ID);
  mqtt.subscribe(topic, 1);

  Serial.println("[MQTT] Conectado y suscrito");
  publicarPing();
  return true;
}

void conectarWifi() {
  Serial.printf("[WiFi] Conectando a %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long inicio = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - inicio > WIFI_TIMEOUT_MS) {
      Serial.println("\n[WiFi] Timeout — reiniciando");
      ESP.restart();
    }
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\n[WiFi] Conectado, IP: %s\n", WiFi.localIP().toString().c_str());
}

// ── Ciclo principal ───────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  Serial.printf("\n=== Controlador de casilleros %s ===\n", CONTROLADOR_ID);

  pinMode(PIN_LED_ESTADO, OUTPUT);
  for (int i = 0; i < NUM_PUERTOS; i++) {
    pinMode(PIN_RELE[i], OUTPUT);
    releEscribir(i, false);  // todos los relés apagados al arrancar
    if (USAR_SENSORES) pinMode(PIN_SENSOR[i], INPUT_PULLUP);
  }

  conectarWifi();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMensaje);
  mqtt.setKeepAlive(60);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) conectarWifi();

  if (!mqtt.connected()) {
    digitalWrite(PIN_LED_ESTADO, LOW);
    if (millis() - ultimoIntentoMqtt > MQTT_REINTENTO_MS) {
      ultimoIntentoMqtt = millis();
      conectarMqtt();
    }
  } else {
    digitalWrite(PIN_LED_ESTADO, HIGH);
    mqtt.loop();
  }

  // Apagar relés cuya duración de apertura expiró (no bloqueante)
  unsigned long ahora = millis();
  for (int i = 0; i < NUM_PUERTOS; i++) {
    if (releApagaEn[i] != 0 && ahora >= releApagaEn[i]) {
      releEscribir(i, false);
      releApagaEn[i] = 0;
      Serial.printf("[RELE] Puerto %d cerrado\n", i + 1);
    }
  }

  // Heartbeat periódico (alimenta controladores.ultimo_ping en el futuro)
  if (mqtt.connected() && ahora - ultimoPing > PING_INTERVALO_MS) {
    ultimoPing = ahora;
    publicarPing();
  }
}
