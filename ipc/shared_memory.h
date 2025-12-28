#pragma once

#include <stddef.h>

struct SharedMemory {
    int fd;
    size_t size;
    void* base;
};

int sm_create(struct SharedMemory* sm, const char* name, size_t size);
int sm_attach(struct SharedMemory* sm, const char* name);
void sm_close(struct SharedMemory* sm);