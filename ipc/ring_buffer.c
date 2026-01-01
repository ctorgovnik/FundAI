#include "ring_buffer.h"

#include <stdlib.h>
#include <string.h>

void rb_init(struct RingBuffer* rb, struct RingBufferHeader* header, void* data, size_t elem_size, size_t capacity) {
    rb->header = header;
    rb->data = data;
    rb->header->write_seq = 0;
    rb->header->read_seq = 0;
    rb->header->capacity = capacity;
    rb->elem_size = elem_size;
}

int rb_write(struct RingBuffer* rb, const void* data) {
    /* SPSC invariant:
    * - write_seq written only by producer
    * - read_seq written only by consumer
    */
    uint64_t write_seq = rb->header->write_seq;
    uint64_t read_seq = rb->header->read_seq;

    /* buffer is full */
    if (write_seq - read_seq == rb->header->capacity) {
        return -1;
    }

    /* write to next slot */
    uint64_t index = write_seq % rb->header->capacity;

    char* slot = (char*)rb->data + index * rb->elem_size;

    /* copy data to slot */
    memcpy(slot, data, rb->elem_size);

    rb->header->write_seq = write_seq + 1;
    return 0;
}

int rb_read(struct RingBuffer* rb, void* data) {
    uint64_t write_seq = rb->header->write_seq;
    uint64_t read_seq = rb->header->read_seq;

    /* buffer is empty */
    if (write_seq == read_seq) {
        return -1;
    }  

    /* read from next slot */
    uint64_t index = read_seq % rb->header->capacity;
    char* slot = (char*)rb->data + index * rb->elem_size;

    /* copy data from slot */
    memcpy(data, slot, rb->elem_size);

    rb->header->read_seq = read_seq + 1;
    return 0;
}

