#ifndef PROXY_PPC_H
#define PROXY_PPC_H

#ifndef URL_MAX_SIZE
#define URL_MAX_SIZE 512
#endif // URL_MAX_SIZE

#include "String.h"

void ApplyProxyPPC(cc_string* url);

#endif // PROXY_PPC_H
