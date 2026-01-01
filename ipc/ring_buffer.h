#pragma once

#include <stdint.h>
#include <stddef.h>

struct RingBufferHeader {
    uint64_t write_seq;
    uint64_t read_seq;
    uint64_t capacity;
};

/* Generic ring buffer view */
struct RingBuffer {
    struct RingBufferHeader* header;
    void* data;
    size_t elem_size;
};

void rb_init(struct RingBuffer* rb, struct RingBufferHeader* header, void* data, size_t elem_size, size_t capacity);
int rb_write(struct RingBuffer* rb, const void* data);
int rb_read(struct RingBuffer* rb, void* data);
