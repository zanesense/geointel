<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Dependencies-Rich%2C%20Cloudscraper%2C%20Tqdm-brightgreen" alt="Dependencies">
</p>

# 🌍 GeoIntel: Proxy-Assisted IP Geolocation & Intelligence

## 💡 Overview

**GeoIntel** is a powerful, refactored, and enhanced tool for gathering comprehensive geolocation and intelligence data on any target IP address or hostname.

Forget relying on a single, rate-limited API. GeoIntel uses an **adaptive proxy rotation system** to bypass detection, scrape fresh proxies, and seamlessly merge data from multiple high-quality geolocation APIs like `ip-api.com` and `ipwho.is`. It even includes robust handling for **Cloudflare** challenges and integrates **OpenCage** for precise reverse-geocoding.

Whether you're performing reconnaissance, analyzing network traffic, or just curious about an IP's origin, GeoIntel delivers fast, consolidated, and detailed results.

---

## ✨ Key Features

* **🛡️ Proxy Powerhouse:** Scrapes fresh, verified HTTP/S proxies from multiple online sources and conducts a full **socket + HTTP forwarding test** to ensure reliability.
* **🔄 Adaptive Rotation:** Uses a built-in proxy rotation system with `cloudscraper` fallback to reliably fetch data and navigate **Cloudflare protection** and rate limits.
* **📊 Data Fusion:** Intelligently **merges geolocation data** from `ip-api.com` and `ipwho.is` for the most complete result set.
* **🗺️ Reverse Geocoding:** Integrates with **OpenCage Geocoding API** for detailed address-level reverse lookups (requires API key).
* **⚡ High Performance:** Utilizes an **adaptive thread pool** based on CPU count for fast proxy verification and concurrent data fetching.
* **💾 Smart Proxy Management:** Saves and reuses known **working proxies** to speed up subsequent scans.
* **🪵 Structured Logging:** Logs detailed activity to a file (`geointel.log`) and the console for easy debugging and tracking.
* **💻 Clean CLI:** A minimal, clear, and engaging command-line interface powered by `rich`.

---

## 🚀 Installation

### Prerequisites

* Python 3.8+

### Steps

1.  **Clone the repository (if applicable) and navigate into the directory.**
2.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You'll need to create a `requirements.txt` file listing the dependencies: `requests`, `cloudscraper`, `beautifulsoup4`, `tqdm`, `rich`, `python-dotenv`, and `concurrent-futures`.)*

---

## ⚙️ Configuration

GeoIntel uses a **`.env`** file for configuration. Create a file named `.env` in the same directory as `main.py`.

### Essential Configuration

| Environment Variable | Default Value | Description |
| :--- | :--- | :--- |
| `OPENCAGE_API_KEY` | (empty string) | **Required for reverse geocoding.** Get a key from OpenCage. |
| `SAVE_WORKING_PROXIES` | `working_proxies.txt` | Path to save/load verified proxies. |
| `MAX_WORKERS` | 50 | Maximum threads for proxy verification/data fetching. |

### Example `.env` file:

```env
# Optional: Get a key from OpenCage to enable reverse geocoding
OPENCAGE_API_KEY="YOUR_OPENCAGE_API_KEY_HERE"

# Optional: Adjust proxy scraping sources (comma-separated URLs)
# PROXY_SOURCES="[https://free-proxy-list.net/,https://www.sslproxies.org/](https://free-proxy-list.net/,https://www.sslproxies.org/)"

# Optional: Log file location
# LOG_FILE="geointel.log"
````

-----

## 🎯 Usage

### Basic Scan (Auto-Detect Your IP)

If you run the tool without a target, it will automatically detect and geolocate your public IP address.

```bash
python3 main.py
```

### Scan a Specific Target

Provide an IP address or hostname using the `--target` flag.

```bash
python3 main.py --target 8.8.8.8
# or
python3 main.py -t example.com
```

### Command Line Options

| Flag | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--target`, `-t` | String | None | Target IP or hostname. |
| `--no-opencage` | Flag | False | Skip OpenCage reverse geocoding, even if the key is set. |
| `--threads` | Integer | Adaptive | Manually set max worker threads. |
| `--timeout` | Integer | 10 | Request timeout in seconds. |
| `--debug` | Flag | False | Enable verbose debug logging. |

-----

## 🛑 Disclaimer

**Use this tool responsibly and legally.** GeoIntel is designed for security professionals and network administrators. Only use it on networks and targets that you own or have explicit, written permission to test. The developers are not responsible for misuse.
