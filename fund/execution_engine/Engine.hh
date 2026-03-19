#pragma once

#include "config.hh"

#include <boost/asio.hpp>

namespace fund {

class Engine {
public:
    explicit Engine(const Config& config);
    void exec();

private:
    Config config_;
    boost::asio::io_context io_; 
};

}

