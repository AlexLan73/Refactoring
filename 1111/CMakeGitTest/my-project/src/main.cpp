#include <iostream>
#include "network/network.hpp"
#include "protocol/protocol.hpp"

int main() {
    // network v2.0.0: ping + connect + disconnect
    auto reply = network::ping("localhost");
    bool ok    = network::connect("localhost", 8080);
    network::disconnect("localhost");

    // protocol v2.0.0: encode + decode + validate
    auto frame   = protocol::encode(reply);
    auto decoded = protocol::decode(frame);
    bool valid   = protocol::validate(frame);

    std::cout << "ping:     " << reply   << "\n";
    std::cout << "connect:  " << ok      << "\n";
    std::cout << "frame:    " << frame   << "\n";
    std::cout << "decoded:  " << decoded << "\n";
    std::cout << "valid:    " << valid   << "\n";

    return 0;
}
