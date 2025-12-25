#pragma once

#include <cstdint>

struct AgentActionV1 {
    int32_t instrument_id;
    double target_position;
};