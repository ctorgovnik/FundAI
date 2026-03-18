#include <iostream>

#include "config.hh"

#include <Engine.hh>

using namespace fund;

int main(int argc, char* argv[]) {
  
  if (argc < 2) {
    std::cerr << "usage: fund_os <config.json>\n";
    return 1;
  }
  
  try {
    auto config = load(argv[1]);
    Engine engine(config);
    engine.exec();
  } catch (const std::exception& e) {
    std::cerr << "fatal: " << e.what() << "\n";
    return 1;
  }

  return 0;
}
