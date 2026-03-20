#pragma once

#include <boost/asio.hpp>
#include <memory>

#include "config.hh"
#include "market_event.hh"

namespace fund {

// Abstract feed handler — public API.
// Subclasses ingest data from a specific transport and post MarketEvents
// to the io_context for processing on the main thread.
// Thread safety: handle_data() runs on a dedicated listener thread.
//                Posting to io_ is thread-safe.
class FeedHandler {
public:
    explicit FeedHandler(boost::asio::io_context& io) : io_{io} {}
    virtual ~FeedHandler() = default;

    // Blocking call — runs the ingestion loop until shutdown.
    // Implementations must post MarketEvents to io_ via boost::asio::post().
    virtual void handle_data() = 0;

protected:
    boost::asio::io_context& io_;
};

// Factory — config decides the transport, Engine never sees the concrete type.
std::unique_ptr<FeedHandler> make_feed_handler(
    const Config& config,
    boost::asio::io_context& io
);

} // namespace fund
