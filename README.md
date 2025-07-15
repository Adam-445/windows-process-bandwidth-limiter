# Windows Network Throttler

![License: MIT](https://img.shields.io/badge/license-MIT-green.svg) ![Version: 2.0.0](https://img.shields.io/badge/version-2.0.0-blue.svg) ![Python: 3.7+](https://img.shields.io/badge/python-3.7%2B-yellow.svg) ![Project Status](https://img.shields.io/badge/status-archived-lightgrey)

*Simulate bandwidth, latency, and packet loss on specific Windows processes for testing, debugging, and educational purposes.*

---

## Features

* **Bandwidth limiting** (Mbps)
* **Latency simulation** (ms)
* **Packet loss simulation** (%)
* **Process-specific targeting** by name substring
* **Hotkey controls** for toggling and exiting
* **Configurable** via JSON or Python settings

## Use Cases

* Testing application performance under constrained or unstable networks
* Simulating mobile or satellite network conditions
* QA and edge-case scenario testing
* Demonstrating networking concepts in educational settings

## Requirements

* Windows 10+ (Admin privileges required)
* Python 3.7 or newer
* Dependencies listed in `requirements.txt`:

  ```bash
  psutil
  pydivert
  keyboard
  ```

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Adam-445/windows-network-throttler.git
cd windows-network-throttler
pip install -r requirements.txt
```

## ⚙Configuration

Configure via the default Python settings or a `config.json` file in the project root.

### Python Settings (`src/config/settings.py`)

Adjust default values in the `ThrottlingConfig` dataclass:

```python
# Example defaults
config = ThrottlingConfig(
    target_bandwidth_mbps=2.0,
    lag_delay_ms=10,
    packet_drop_rate=0.0,
    process_name_substring="RobloxPlayer",
    toggle_key="f1",
    exit_key="esc",
)
```

### JSON Configuration (`config.json`)

```json
{
  "target_bandwidth_mbps": 1.5,
  "lag_delay_ms": 100,
  "packet_drop_rate": 0.05,
  "process_name_substring": "your_process",
  "toggle_key": "f1",
  "exit_key": "esc"
}
```

> **Note:** JSON settings override Python defaults when present.

## Usage

Run the tool with administrator privileges:

```bash
python -m main
```

Upon launch, the application will:

1. Verify administrator privileges
2. Load configuration
3. Detect and attach to the target process
4. Listen for network packets and hotkeys

### Hotkeys

| Key | Action                   |
| --- | ------------------------ |
| F1  | Toggle throttling ON/OFF |
| ESC | Exit the application     |

## 📝 Logging & Output

* **Console**: real-time status updates (processed, throttled, dropped, rate)
* **Log file**: if `log_file` is set in config, detailed logs will be written

## Troubleshooting

1. Ensure you run as **Administrator**.
2. Verify `WinDivert.dll` is in the project directory and matches your Python architecture (x86/x64).
3. Disable or configure antivirus/Windows Defender if packet capture fails.
4. Reduce the number of target ports in config if complex filters error.
5. Check dependencies are installed: `psutil`, `pydivert`, `keyboard`.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.

---

*Developed by Adam-445*
