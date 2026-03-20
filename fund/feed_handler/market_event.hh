#pragma once

#include <cstdint>

namespace fund {

// Normalized market event — transport-agnostic.
// Posted to io_context by FeedHandler implementations.
struct MarketEvent {
    int32_t instrument_id;
    double  bid;
    double  ask;
    double  mid;
    double  volume;
    int64_t timestamp_ns; // nanoseconds since Unix epoch
};

} // namespace fund
