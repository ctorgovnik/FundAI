#include "Engine.hh"

namespace fund {

Engine::Engine(const Config& config)
   : config_(config),
     feed_handler_(make_feed_handler(config_, io_))
{
}

void Engine::exec() { 
  io_.run();
}

}
