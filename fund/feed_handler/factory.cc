#include "feed_handler.hh"
#include "sim/sim_feed_handler.hh"
#include "live/live_feed_handler.hh"

#include <stdexcept>

namespace fund {

std::unique_ptr<FeedHandler> make_feed_handler(
    const Config& config,
    boost::asio::io_context& io
) {
    if (config.mode == "simulation") {
        return std::make_unique<SimFeedHandler>(io);
    } else if (config.mode == "live") {
        return std::make_unique<LiveFeedHandler>(io);
    }
    throw std::invalid_argument("unknown mode: " + config.mode);
}

} // namespace fund
