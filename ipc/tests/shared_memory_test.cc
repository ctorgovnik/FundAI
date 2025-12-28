#include <gtest/gtest.h>

#include <sys/mman.h>

extern "C" {
#include "shared_memory.h"
}

class SharedMemoryTest : public ::testing::Test {
protected:
    std::string shmem_name;

    void SetUp() override {
        shmem_name = "/test_shmem";
    }

    void TearDown() override {
        shm_unlink(shmem_name.c_str());
    }
};

TEST_F(SharedMemoryTest, Create) {
    struct SharedMemory sm;
    ASSERT_EQ(sm_create(&sm, shmem_name.c_str(), 1024), 0);
    ASSERT_EQ(sm.size, 1024);
    ASSERT_GT(sm.fd, 0);
    sm_close(&sm);
}

TEST_F(SharedMemoryTest, AttachBeforeCreate) {
    struct SharedMemory sm;
    ASSERT_EQ(sm_attach(&sm, shmem_name.c_str()), -1);
}

TEST_F(SharedMemoryTest, CreateAndAttach) {
    struct SharedMemory sm1;
    ASSERT_EQ(sm_create(&sm1, shmem_name.c_str(), 1024), 0);
    ASSERT_GE(sm1.fd, 0);

    int* ptr = static_cast<int*>(sm1.base);
    *ptr = 42;

    struct SharedMemory sm2;
    ASSERT_EQ(sm_attach(&sm2, shmem_name.c_str()), 0);
    ASSERT_GE(sm2.fd, 0);

    int* ptr2 = static_cast<int*>(sm2.base);
    ASSERT_EQ(*ptr2, 42);

    sm_close(&sm1);
    sm_close(&sm2);
}