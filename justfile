build_dir := "build"

# Configure (only needed once or when CMakeLists.txt changes)
configure:
    cmake -B {{build_dir}} -G Ninja -DCMAKE_BUILD_TYPE=Debug

# Build all targets
build:
    cmake --build {{build_dir}}

# Build and run all tests
test: build
    ctest --test-dir {{build_dir}} --output-on-failure

# Configure, build, and test from scratch
all: configure test

# Remove build artifacts
clean:
    rm -rf {{build_dir}}
