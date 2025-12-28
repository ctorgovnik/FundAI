#include "shared_memory.h"

#include <sys/mman.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

int sm_create(struct SharedMemory* sm, const char* name, size_t size) {
    int fd = shm_open(name, O_CREAT | O_RDWR, 0666);
    if (fd == -1) {
        return -1;
    }

    /* truncate file to size */
    if (ftruncate(fd, size) == -1) {
        close(fd);
        return -1;
    }

    void* addr = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

    if (addr == MAP_FAILED) {
        close(fd);
        return -1;
    }

    sm->fd = fd;
    sm->size = size;
    sm->base = addr;
    return 0;
}

int sm_attach(struct SharedMemory* sm, const char* name) {
    int fd = shm_open(name, O_RDWR, 0666);
    if (fd == -1) {
        return -1;
    }

    struct stat st;
    if (fstat(fd, &st) == -1) {
        close(fd);
        return -1;
    }

    void* addr = mmap(NULL, st.st_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (addr == MAP_FAILED) {
        close(fd);
        return -1;
    }

    sm->fd = fd;
    sm->size = st.st_size;
    sm->base = addr;
    return 0;
}

void sm_close(struct SharedMemory* sm) {
    munmap(sm->base, sm->size);
    close(sm->fd);
}