// ══════════════════════════════════════════════════════════════
//  Configuración del controlador ESP32 — Casilleros Automatizados
//  Copiar este archivo como config.h y ajustar ANTES de flashear.
//  config.h está en .gitignore: nunca subir credenciales reales.
// ══════════════════════════════════════════════════════════════
#ifndef CONFIG_H
#define CONFIG_H

// ── Identidad del controlador ────────────────────────────────
// Debe coincidir con controladores.id en la base de datos
#define CONTROLADOR_ID      "CTRL-P1"

// ── WiFi (red de 2.4 GHz; el ESP32 no soporta 5 GHz) ─────────
#define WIFI_SSID           "CAMBIAR_SSID"
#define WIFI_PASSWORD       "CAMBIAR_PASSWORD"

// ── Broker MQTT (Mosquitto del docker-compose) ───────────────
#define MQTT_HOST           "192.168.1.100"  // IP del servidor que corre docker
#define MQTT_PORT           1883
#define MQTT_USER           "casilleros"
#define MQTT_PASSWORD       "CAMBIAR_MQTT_PASSWORD"  // ver MQTT_PASSWORD en .env del servidor

// ── Hardware ──────────────────────────────────────────────────
#define NUM_PUERTOS         5      // Casilleros conectados a esta placa (max 8)

// GPIO de los relés, en orden: puerto 1, 2, 3, ... (índice 0 = puerto 1)
static const int PIN_RELE[NUM_PUERTOS] = {16, 17, 18, 19, 21};

// true si el módulo de relés se activa con nivel BAJO (típico en módulos chinos de 5V)
#define RELE_ACTIVO_BAJO    true

// Sensores de puerta (reed switch) — opcional. Poner USAR_SENSORES en false si no hay.
#define USAR_SENSORES       false
static const int PIN_SENSOR[NUM_PUERTOS] = {25, 26, 27, 32, 33};

// LED de estado de la placa (GPIO 2 = LED azul integrado en la mayoría de dev-kits)
#define PIN_LED_ESTADO      2

// ── Tiempos ───────────────────────────────────────────────────
#define APERTURA_DEFAULT_S  5      // Si el backend no manda duracion_segundos
#define PING_INTERVALO_MS   30000  // Heartbeat hacia el backend
#define WIFI_TIMEOUT_MS     20000
#define MQTT_REINTENTO_MS   5000

#endif
