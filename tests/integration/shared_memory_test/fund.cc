
extern "C"{
#include <ring_buffer.h>
#include <shared_memory.h>
}

#include <sys/mman.h>
#include <iostream>

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

  void dispatch_data(const int& instrument_id, const double& close_price){
    
    FundData data{instrument_id, close_price};

    int result = rb_write(&fund_data, &data);
    
    if (result == 0){
      std::cout << "Fund wrote instrumend id " << instrument_id << " with close price "
        << close_price << " to shared mem\n";
    } else {
      std::cout << "Ring Buffer full. Waiting for reader.\n";
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
    fund.dispatch_data(instrument_id, close_price);
    instrument_id++;
    close_price += 2;
  }

  return 0;
}

