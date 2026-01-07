from pythonosc import dispatcher, osc_server, udp_client
import socket

_server = None
_clients = []


def start_osc_forwarder(config, log_fn):
    global _server, _clients

    recv_ip = config.get("receive_address", "0.0.0.0")
    recv_port = config.get("receive_port", 9001)
    targets = config.get("forward_targets", [])

    if not targets or len(targets) > 5:
        log_fn("[ERROR] forward_targets must contain 1 to 5 ports.")
        return False

    # -----------------------------
    # 1. 送信クライアントの作成（例外処理つき）
    # -----------------------------
    _clients = []
    for port in targets:
        try:
            client = udp_client.SimpleUDPClient("127.0.0.1", port)
            _clients.append(client)
        except Exception as e:
            log_fn(f"[WARN] Could not create UDP client for port {port}: {e}")

    if not _clients:
        log_fn("[ERROR] No valid forward target ports. Aborting.")
        return False

    # -----------------------------
    # 2. 受信サーバーの作成（例外処理つき）
    # -----------------------------
    disp = dispatcher.Dispatcher()

    def handler(address, *args):
        log_fn(f"Received {address} {args}")
        for client in _clients:
            try:
                client.send_message(address, args)
            except Exception as e:
                log_fn(f"[WARN] Failed to send to a client: {e}")

    disp.set_default_handler(handler)

    try:
        _server = osc_server.ThreadingOSCUDPServer((recv_ip, recv_port), disp)
    except OSError as e:
        log_fn(f"[ERROR] Could not bind to {recv_ip}:{recv_port}: {e}")
        return False

    log_fn(f"Listening on {recv_ip}:{recv_port} → {targets}")

    try:
        _server.serve_forever()
    except Exception as e:
        log_fn(f"[ERROR] Server stopped unexpectedly: {e}")
        return False

    return True


def stop_osc_forwarder():
    if _server:
        _server.shutdown()


def cleanup_osc_server():
    global _server
    if _server:
        _server.server_close()
        _server = None
