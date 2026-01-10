from pythonosc import dispatcher, osc_server, udp_client
import socket

_server = None
_clients = []
_valid_ports = []


# ---------------------------------------------------------
# 1. validate_ports()  ← 起動前チェックのみ（bind しない）
# ---------------------------------------------------------
def validate_ports(config, log_fn):
    global _valid_ports

    recv_ip = config.get("receive_address", "0.0.0.0")
    recv_port = config.get("receive_port", 9001)
    targets = config.get("forward_targets", [])

    _valid_ports = []
    invalid_ports = []

    # -----------------------------
    # 送信ポートの妥当性チェック
    # -----------------------------
    for port in targets:
        try:
            port = int(port)
            if not (1 <= port <= 65535):
                raise ValueError("Port out of range")
            # UDPClient は bind しないのでここでは作らない
            _valid_ports.append(port)
        except Exception as e:
            invalid_ports.append((port, str(e)))
            log_fn(f"[WARN] Invalid forward port {port}: {e}")

    if not _valid_ports:
        log_fn("[ERROR] No valid forward target ports.")
        return False, []

    # -----------------------------
    # 受信ポートが bind できるかだけ確認（サーバー起動しない）
    # -----------------------------
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((recv_ip, recv_port))
        sock.close()
    except Exception as e:
        log_fn(f"[ERROR] Cannot bind receive port {recv_port}: {e}")
        return False, []

    return True, _valid_ports


# ---------------------------------------------------------
# 2. run_forwarder()  ← スレッドで 1 回だけ起動（bind する）
# ---------------------------------------------------------
def run_forwarder(config, log_fn):
    global _server, _clients, _valid_ports

    recv_ip = config.get("receive_address", "0.0.0.0")
    recv_port = config.get("receive_port", 9001)

    # validate_ports() で確定した _valid_ports を使う想定
    _clients = []
    for port in _valid_ports:
        try:
            client = udp_client.SimpleUDPClient("127.0.0.1", port)
            _clients.append(client)
        except Exception as e:
            log_fn(f"[WARN] Could not create UDP client for port {port}: {e}")

    if not _clients:
        log_fn("[ERROR] No usable forward ports at runtime. Aborting.")
        return

    # -----------------------------
    # OSC サーバー起動（ここで bind）
    # -----------------------------
    disp = dispatcher.Dispatcher()

    def handler(address, *args):
        # ★ DEBUG=True の時は全受信データをログに出す（log_fn 側で DEBUG 判定）
        log_fn(f"[RECV] addr={address}, args={args}")
        for client in _clients:
            try:
                client.send_message(address, args)
            except Exception as e:
                log_fn(f"[WARN] Failed to send to a client: {e}")

    disp.set_default_handler(handler)

    try:
        _server = osc_server.ThreadingOSCUDPServer((recv_ip, recv_port), disp)
    except Exception as e:
        log_fn(f"[ERROR] Could not bind to {recv_ip}:{recv_port}: {e}")
        return

    log_fn(f"Listening on {recv_ip}:{recv_port} → valid: {_valid_ports}")

    try:
        _server.serve_forever()
    except Exception as e:
        log_fn(f"[ERROR] Server stopped unexpectedly: {e}")


# ---------------------------------------------------------
# 3. 停止処理
# ---------------------------------------------------------
def stop_osc_forwarder():
    if _server:
        _server.shutdown()


def cleanup_osc_server():
    global _server
    if _server:
        _server.server_close()
        _server = None
