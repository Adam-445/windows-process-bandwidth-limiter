# Windows Network Throttler

A professional-grade network throttling application for Windows that simulates network conditions (bandwidth limiting, latency, packet loss) for specific processes.

## Features
- Bandwidth limiting (Mbps)
- Latency simulation (ms)
- Packet loss simulation (%)
- Process-specific targeting
- Hotkey controls (toggle on/off, exit)

## Requirements
- Python 3.7+
- Windows OS
- Administrative privileges

## Installation
```bash
git clone https://github.com/Adam-445/windows-process-bandwidth-limiter.git
cd windows-network-throttler
pip install -r requirements.txt
```

## Usage
```bash
python -m main
```

## Configuration
Modify `src/config/settings.py` or create a `config.json`:
```json
{
  "target_bandwidth_mbps": 1.5,
  "lag_delay_ms": 100,
  "packet_drop_rate": 0.05,
  "process_name_substring": "your_process"
}
```

## Controls
- F1: Toggle throttling
- ESC: Exit application
