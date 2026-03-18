#pragma once

#include <string>

namespace fund {

struct Config {
  std::string mode;
};

inline Config load(const std::string& path) {
  return Config{"sim"};
}

}
