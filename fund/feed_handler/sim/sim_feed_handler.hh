#pragma once

#include "feed_handler.hh"

namespace fund {

class SimFeedHandler : public FeedHandler {
public:
    explicit SimFeedHandler(boost::asio::io_context& io) : FeedHandler(io) {}

    // TODO(#9): drive from simulation engine historical replay
    void handle_data() override;
};

} // namespace fund
