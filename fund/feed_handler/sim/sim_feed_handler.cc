#include "sim_feed_handler.hh"
#include "market_event.hh"

#include <boost/asio.hpp>
#include <chrono>

namespace fund {

void SimFeedHandler::handle_data() {
    // TODO(#9): replace with historical bar replay
    // Synthetic tick for now so the event loop has something to process
    MarketEvent event{
        .instrument_id = 1,
        .bid           = 99.9,
        .ask           = 100.1,
        .mid           = 100.0,
        .volume        = 1000.0,
        .timestamp_ns  = std::chrono::duration_cast<std::chrono::nanoseconds>(
                             std::chrono::system_clock::now().time_since_epoch()
                         ).count(),
    };

    boost::asio::post(io_, [event] {
        // TODO: dispatch to state update handler
        (void)event;
    });
}

} // namespace fund
