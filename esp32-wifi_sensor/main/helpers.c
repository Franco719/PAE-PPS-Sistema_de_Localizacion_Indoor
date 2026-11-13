#include <stdio.h>
#include "helpers.h"
#include "esp_http_client.h"
#include "cJSON.h"
#include "esp_wifi.h"
#include "esp_log.h"
#include "config.h"

void send_data_to_server(wifi_ap_record_t *records, int cant)
{
    // 1. Crear el objeto JSON en memoria usando cJSON
    cJSON *root = cJSON_CreateObject();

    // Agregar el identificador del nodo
    cJSON_AddNumberToObject(root, "nodo_id", NODO_ID);

    // Crear el array de redes
    cJSON *networks = cJSON_CreateArray();
    cJSON_AddItemToObject(root, "networks", networks);

    for(int i = 0; i < cant; i++) {

        // Validación A: Si el SSID está vacío (primer caracter es fin de cadena), lo salteamos
        if (records[i].ssid[0] == '\0') {
            continue;
        }

        // Validación B: Verificar que el SSID solo tenga caracteres legibles (ASCII 32 al 126)
        bool valid_ssid = true;

        for (int j = 0; j < sizeof(records[i].ssid) && records[i].ssid[j] != '\0'; j++) {
            char c = records[i].ssid[j];

            if (c < 32 || c > 126) {
                valid_ssid = false;
                break; // Carácter basura detectado
            }
        }

        // Convierto el BSSID a string
        char bssid_str[18];

        snprintf(
            bssid_str,
            sizeof(bssid_str),
            "%02X:%02X:%02X:%02X:%02X:%02X",
            records[i].bssid[0],
            records[i].bssid[1],
            records[i].bssid[2],
            records[i].bssid[3],
            records[i].bssid[4],
            records[i].bssid[5]
        );

        // Si pasó los filtros, lo agregamos de forma segura al JSON
        if (valid_ssid) {
            cJSON *item = cJSON_CreateObject();

            cJSON_AddStringToObject(item, "ssid", (char*)records[i].ssid);
            cJSON_AddStringToObject(item, "bssid", bssid_str);
            cJSON_AddNumberToObject(item, "rssi", records[i].rssi);

            cJSON_AddItemToArray(networks, item);
        }
    }

    // Convertir el JSON a string
    char *post_data = cJSON_PrintUnformatted(root);

    // 2. Configurar el cliente HTTP de ESP-IDF
    esp_http_client_config_t config = {
        .url = SERVER_LOCATE_IP,
        .method = HTTP_METHOD_POST,
    };

    esp_http_client_handle_t client = esp_http_client_init(&config);

    // Para HTTPS, no funciona pero es por aca
    /*esp_http_client_config_t config = {
        .url = SERVER_LOCATE_IP,
        .transport_type = HTTP_TRANSPORT_OVER_SSL,
        .method = HTTP_METHOD_POST,
        .crt_bundle_attach = esp_crt_bundle_attach,
    };
    esp_http_client_handle_t client = esp_http_client_init(&config);*/

    // Encabezados HTTP
    esp_http_client_set_header(client, "API-Key", API_SECRET_KEY);
    esp_http_client_set_header(client, "Content-Type", "application/json");

    esp_http_client_set_post_field(client, post_data, strlen(post_data));

    // 3. Ejecutar el envío
    esp_err_t err = esp_http_client_perform(client);

    if (err == ESP_OK) {
        ESP_LOGI(
            APP_TAG,
            "Datos enviados correctamente. Código HTTP: %d",
            esp_http_client_get_status_code(client)
        );
    }

    // 4. Liberar recursos
    esp_http_client_cleanup(client);
    cJSON_Delete(root);
    free(post_data);
}