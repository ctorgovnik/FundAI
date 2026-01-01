#include <gtest/gtest.h>

#include <sys/mman.h>

extern "C"{
#include "ring_buffer.h"
#include "shared_memory.h"
}

class RingBufferTest : public ::testing::Test {
  protected:
    std::string shmem_name;
    RingBuffer rb;
    SharedMemory sm;

    void SetUp() override {
     shmem_name = "/test_shmem"; 
     sm_create(&sm, shmem_name.c_str(), sizeof(RingBufferHeader) + 1024);
  
     RingBufferHeader* rb_header = static_cast<RingBufferHeader*>(sm.base);
     void* data = static_cast<char*>(sm.base) + sizeof(RingBufferHeader); 

     rb_init(&rb, rb_header, data, 4, 1024);
  
     EXPECT_EQ(rb.header->write_seq, 0);
     EXPECT_EQ(rb.header->read_seq, 0);
     EXPECT_EQ(rb.header->capacity, 1024);
  
     EXPECT_EQ(rb.elem_size, 4);
     EXPECT_EQ(rb.data, data);

    }
    
    void TearDown() override {
      sm_close(&sm);
      shm_unlink(shmem_name.c_str());
    }
};



TEST_F(RingBufferTest, WriteRead) { 
  
  int test_data = 4;
  ASSERT_EQ(rb_write(&rb, &test_data), 0);
  
  int data;

  ASSERT_EQ(rb_read(&rb, &data), 0);

  ASSERT_EQ(data, 4);
}
