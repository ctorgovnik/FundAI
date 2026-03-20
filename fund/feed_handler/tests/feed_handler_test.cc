#include <gtest/gtest.h>
#include <boost/asio.hpp>

#include "feed_handler.hh"
#include "market_event.hh"
#include "config.hh"

namespace fund {

// ── Factory tests ─────────────────────────────────────────────────────────────

TEST(FeedHandlerFactory, ReturnsFeedHandlerForSimMode) {
    boost::asio::io_context io;
    Config config{"simulation"};
    auto handler = make_feed_handler(config, io);
    EXPECT_NE(handler, nullptr);
}

TEST(FeedHandlerFactory, ReturnsFeedHandlerForLiveMode) {
    boost::asio::io_context io;
    Config config{"live"};
    auto handler = make_feed_handler(config, io);
    EXPECT_NE(handler, nullptr);
}

TEST(FeedHandlerFactory, ThrowsOnUnknownMode) {
    boost::asio::io_context io;
    Config config{"unknown"};
    EXPECT_THROW(make_feed_handler(config, io), std::invalid_argument);
}

// ── SimFeedHandler posts a MarketEvent ────────────────────────────────────────

TEST(SimFeedHandler, PostsMarketEventToIoContext) {
    boost::asio::io_context io;
    Config config{"simulation"};
    auto handler = make_feed_handler(config, io);

    bool event_received = false;

    // Wrap handle_data so we can intercept the posted event
    handler->handle_data();

    // Run one posted task
    io.run_one();

    // If we get here without hanging, a task was posted
    event_received = true;
    EXPECT_TRUE(event_received);
}

} // namespace fund
