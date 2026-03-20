
extern "C"{
#include <ring_buffer.h>
#include <shared_memory.h>
}

#include <sys/mman.h>
#include <chrono>
#include <iostream>
#include <thread>

struct FundData {
  int instrument_id;
  double close_price;
};


class SimpleFund {
  
  //FundData last_data;
  RingBuffer fund_data;
  SharedMemory shmem;
  const char* shmem_name;

public:
  
  SimpleFund(const char* shmem_name) 
    : shmem_name(shmem_name) 
  {
    
    size_t capacity = 4;
    size_t shmem_size = sizeof(RingBufferHeader) + (capacity * sizeof(FundData));
    if (sm_create(&shmem, shmem_name, shmem_size) == -1){
      std::cerr << "Failed to create shared memory: " << shmem_name << ".\n";
      std::runtime_error("Shared memory creationf failed"); 
    }
    
    RingBufferHeader* rb_header = static_cast<RingBufferHeader*>(shmem.base);

    void* data = static_cast<char*>(shmem.base) + sizeof(RingBufferHeader);

    rb_init(&fund_data, rb_header, data, sizeof(FundData), capacity);
    
  }

  ~SimpleFund(){
    sm_close(&shmem);
    shm_unlink(shmem_name);
    std::cout << "Closed shared memory" << std::endl;
  }

  // Writes one item, blocking until space is available (up to timeout_ms).
  // Returns true on success, false on timeout.
  bool dispatch_data(const int& instrument_id, const double& close_price,
                     int timeout_ms = 5000) {
    FundData data{instrument_id, close_price};

    auto deadline = std::chrono::steady_clock::now() +
                    std::chrono::milliseconds(timeout_ms);

    while (true) {
      if (rb_write(&fund_data, &data) == 0) {
        std::cout << "Fund wrote instrument_id=" << instrument_id
                  << " close_price=" << close_price << "\n";
        return true;
      }

      if (std::chrono::steady_clock::now() >= deadline) {
        std::cerr << "Timeout: ring buffer full after " << timeout_ms
                  << "ms (instrument_id=" << instrument_id << ")\n";
        return false;
      }

      std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
  }


};

int main(int argc, char *argv[]){
  
  if (argc != 2){
    std::cerr << "Usage: " << argv[0] << " <shmem_name>\n";
    return 1;
  }
  
  SimpleFund fund(argv[1]);
  
  int instrument_id = 1;
  double close_price = 1.0;
  
  for (int i = 0; i < 10; i++){
    if (!fund.dispatch_data(instrument_id, close_price)) {
      return 1;
    }
    instrument_id++;
    close_price += 2;
  }

  return 0;
}

