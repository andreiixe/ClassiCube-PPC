#include <stdlib.h>  // For malloc
#include <string.h> 
#include "ProxyPPC.h"

void ApplyProxyPPC(cc_string* url) {
    const char* proxyPrefix = "http://pikaiixe.duckdns.org:5090/?url=";
    
    // Allocate memory for proxy
    size_t newLength = url->length + strlen(proxyPrefix);
    char* newBuffer = (char*)malloc(newLength + 1); // +1 for the null terminator
    if (newBuffer == NULL) {
        // Memory allocation error handling
        return;
    }
    
    strcpy(newBuffer, proxyPrefix);
    strcat(newBuffer, url->buffer);
    
    free(url->buffer); // Release the old memory
    url->buffer = newBuffer;
    url->length = newLength;
}
