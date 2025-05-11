# osc_forwarder.py
from pythonosc import dispatcher, osc_server, udp_client

_server = None
_clients = []


def start_osc_forwarder(config, log_fn):
    global _server, _clients

    recv_ip = config.get("receive_address", "0.0.0.0")
    recv_port = config.get("receive_port", 9001)
    targets = config.get("forward_targets", [])
    if not targets or len(targets) > 5:
        log_fn("[ERROR] forward_targets must contain 1 to 5 ports.")
        return

    _clients = [udp_client.SimpleUDPClient("127.0.0.1", port) for port in targets]

    def handler(address, *args):
        log_fn(f"Received {address} {args}")
        for client in _clients:
            client.send_message(address, args)

    disp = dispatcher.Dispatcher()
    disp.set_default_handler(handler)
    _server = osc_server.ThreadingOSCUDPServer((recv_ip, recv_port), disp)
    log_fn(f"Listening on {recv_ip}:{recv_port} → {targets}")
    _server.serve_forever()


def stop_osc_forwarder():
    if _server:
        _server.shutdown()


def cleanup_osc_server():
    global _server
    if _server:
        _server.server_close()
        _server = None
