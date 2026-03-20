#pragma once

#include "feed_handler.hh"

namespace fund {

class LiveFeedHandler : public FeedHandler {
public:
    explicit LiveFeedHandler(boost::asio::io_context& io) : FeedHandler(io) {}

    // TODO: connect to live market data feed
    void handle_data() override;
};

} // namespace fund
