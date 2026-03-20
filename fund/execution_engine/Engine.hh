#pragma once

#include <memory>

#include "config.hh"
#include "feed_handler.hh"

#include <boost/asio.hpp>

namespace fund {

class Engine {
public:
    explicit Engine(const Config& config);
    void exec();

private:
    Config config_;
    boost::asio::io_context io_; 
    std::unique_ptr<FeedHandler> feed_handler_;
};

}

