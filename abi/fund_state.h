#pragma once

#include <cstdint>

struct FundStateV1 {
    int32_t instrument_id;

    // market state (instrument-scoped)
    double mid_price;
    double bid_price;
    double ask_price;
    double volatility;
    double volume;

    // account state (agent-scoped)
    int64_t position;
    double avg_entry_price;
    double unrealized_pnl;
    double realized_pnl;
    double cash;
};