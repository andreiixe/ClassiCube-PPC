#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include "ProxyPPC.h"

void CreateDefaultProxyConfig() {
    FILE* file = fopen("Proxy_server.txt", "r");
    if (file == NULL) {
        file = fopen("Proxy_server.txt", "w");
        if (file != NULL) {
            fprintf(file, "/* ClassiCube-PPC for Mac OS X 10.4+, PPC Proxy developed by Andreiixe */\n");
            fprintf(file, "\n");
            fprintf(file, "Proxy_Server=http://pikaiixe.duckdns.org:5090/?url=\n");
            fprintf(file, "Proxy_online=True\n");
            fclose(file);
        }
    } else {
        fclose(file);
    }
}

bool ReadProxyConfig(char* proxyPrefix, size_t bufferSize, bool* useProxy) {
    FILE* file = fopen("Proxy_server.txt", "r");
    if (file == NULL) {
        return false;
    }

    char line[256];
    while (fgets(line, sizeof(line), file)) {
        if (strncmp(line, "Proxy_Server=", 13) == 0) {
            strncpy(proxyPrefix, line + 13, bufferSize - 1);
            proxyPrefix[bufferSize - 1] = '\0';
            size_t len = strlen(proxyPrefix);
            if (len > 0 && proxyPrefix[len - 1] == '\n') {
                proxyPrefix[len - 1] = '\0';
            }
        } else if (strncmp(line, "Proxy_online=", 13) == 0) {
            *useProxy = (strncmp(line + 13, "True", 4) == 0);
        }
    }

    fclose(file);
    return true;
}

void ApplyProxyPPC(cc_string* url) {
    char proxyPrefix[256] = {0};
    bool useProxy = false;

    CreateDefaultProxyConfig();

    if (!ReadProxyConfig(proxyPrefix, sizeof(proxyPrefix), &useProxy)) {
        return;
    }

    if (!useProxy) {
        return;
    }

    size_t proxyPrefixLength = strlen(proxyPrefix);
    size_t originalUrlLength = url->length;
    size_t newLength = proxyPrefixLength + originalUrlLength;

    if (newLength >= URL_MAX_SIZE) {
        return;
    }

    memmove(url->buffer + proxyPrefixLength, url->buffer, originalUrlLength + 1);
    memcpy(url->buffer, proxyPrefix, proxyPrefixLength);

    url->length = newLength;
}