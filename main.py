# main.py - タスクトレイ常駐型 + OSCフォワーダー（Base64埋め込みアイコン版 + 情報メニュー付き）

import sys
import os
import json
import threading
from datetime import datetime
from pystray import Icon, MenuItem as item, Menu
from PIL import Image, ImageDraw
from io import BytesIO
import base64
from osc_forwarder import start_osc_forwarder, stop_osc_forwarder, cleanup_osc_server

config = {}
log_file = None
icon = None
icon_title = "OSC Forwarder"
state = {}

def load_config():
    global config, log_file, icon_title
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    config_path = os.path.join(base_path, "OSCForwarder.json")
    if not os.path.exists(config_path):
        print(f"[ERROR] Config not found: {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    recv_port = config.get("receive_port", 9001)
    targets = config.get("forward_targets", [])
    exe_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    icon_title = f"{exe_name} - IN:{recv_port} → OUT:{','.join(map(str, targets))}"

    if config.get("DEBUG"):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        log_file = os.path.join(base_path, f"{exe_name}_{timestamp}.log")

def log(message):
    if config.get("DEBUG"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

def resource_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

def create_icon():
    # PyInstaller で同梱した icon.ico を読み込む
    icon_path = resource_path("icon.ico")

    try:
        return Image.open(icon_path)
    except Exception as e:
        print(f"[WARN] Could not load icon.ico: {e}")
        # フォールバックの簡易アイコン
        image = Image.new("RGB", (64, 64), "blue")
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill="white")
        return image

def info_handler(icon, item):
    recv_port = state["recv_port"]
    valid_ports = state["valid_ports"]
    info_text = (
        f"Receive: {recv_port}\n"
        f"Forward: {', '.join(map(str, valid_ports))}"
    )
    icon.notify(info_text, "Current Settings")

def on_quit(icon, item):
    stop_osc_forwarder()
    cleanup_osc_server()
    icon.stop()

if __name__ == "__main__":
    load_config()

    # まず forwarder を「起動せずに」ポート検証だけ行う
    osc_running, valid_ports = validate_ports(config, log)

    if not osc_running:
        log("[ERROR] OSC forwarder failed to start. Exiting.")
        sys.exit(1)

    # info_handler で使えるように保持
    state = {
        "valid_ports": valid_ports,
        "recv_port": config.get("receive_port", 9001),
    }

    # forwarder をバックグラウンドで起動
    threading.Thread(
        target=lambda: start_osc_forwarder(config, log),
        daemon=True
    ).start()

    # タスクトレイアイコン起動
    icon = Icon(
        "osc_forwarder",
        icon=create_icon(),
        title=icon_title,
        menu=Menu(
            item("Info", info_handler),
            item("Exit", on_quit)
        )
    )
    icon.run()
