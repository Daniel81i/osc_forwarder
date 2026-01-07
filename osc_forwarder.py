from pythonosc import dispatcher, osc_server, udp_client
import socket

_server = None
_clients = []
_valid_ports = []   # main から参照できるように保持


def start_osc_forwarder(config, log_fn):
    global _server, _clients, _valid_ports

    recv_ip = config.get("receive_address", "0.0.0.0")
    recv_port = config.get("receive_port", 9001)
    targets = config.get("forward_targets", [])

    # -----------------------------
    # 送信ポートの検証
    # -----------------------------
    _clients = []
    _valid_ports = []
    invalid_ports = []

    for port in targets:
        try:
            client = udp_client.SimpleUDPClient("127.0.0.1", int(port))
            _clients.append(client)
            _valid_ports.append(port)
        except Exception as e:
            invalid_ports.append((port, str(e)))
            log_fn(f"[WARN] Could not create UDP client for port {port}: {e}")

    # 全滅したら終了
    if not _clients:
        log_fn("[ERROR] No valid forward target ports. Aborting.")
        return False, []

    # -----------------------------
    # 受信ポートの検証
    # -----------------------------
    disp = dispatcher.Dispatcher()

    def handler(address, *args):
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
        return False, _valid_ports

    log_fn(f"Listening on {recv_ip}:{recv_port} → valid: {_valid_ports}")

    # サーバー開始
    try:
        _server.serve_forever()
    except Exception as e:
        log_fn(f"[ERROR] Server stopped unexpectedly: {e}")
        return False, _valid_ports

    return True, _valid_ports


def stop_osc_forwarder():
    if _server:
        _server.shutdown()


def cleanup_osc_server():
    global _server
    if _server:
        _server.server_close()
        _server = None
