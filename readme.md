# OSCForwarder

A lightweight background tool that listens for OSC messages on a specified port and forwards them to multiple local ports.  
It runs in the Windows task tray and requires no console interaction.

このツールは指定したOSCポートをリッスンし、複数のローカルポートへデータを転送する軽量な常駐アプリです。  
Windowsのタスクトレイに常駐し、コンソール操作不要で動作します。

---

## Features / 機能

- 🛰️ Forward OSC messages to up to 5 local ports  
  最大5つのローカルポートへのOSC転送が可能  
- 🛠 Configurable via `osc_forward_config.json`  
  `osc_forward_config.json` による設定変更  
- 📜 Hover-free tray interface with Info menu  
  ホバー操作不要の情報表示メニュー付きタスクトレイ  

---

## Configuration / 設定

Create a file named `osc_forward_config.json` in the same directory as the `.exe` file:

`osc_forward_config.json` を `.exe` ファイルと同じ場所に作成してください：

```json
{
  "receive_address": "0.0.0.0",
  "receive_port": 9001,
  "forward_targets": [9002, 9003],
  "DEBUG": true
}

```
## Requires
Requires Python 3.10+

## License
MIT License
