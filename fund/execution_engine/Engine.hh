#pragma once

#include "config.hh"

namespace fund {

class Engine {
public:
    explicit Engine(const Config& config);
    void exec();

private:
    Config config_;
};

}

