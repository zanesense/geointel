# 🌍 GeoIntel: Proxy-Assisted IP Intelligence

**Tired of rate limits blocking your geolocation queries? GeoIntel finds, validates, and uses fresh proxies to bypass API restrictions and give you deep IP insights!**

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python%203.8%2B-blue?style=for-the-badge&logo=python" alt="Python 3.8+ Badge">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License Badge">
  <img src="https://img.shields.io/badge/Dependencies-rich%2C%20requests%2C%20tqdm-brightgreen?style=for-the-badge" alt="Dependencies Badge">
  <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" alt="Status Active Badge">
</p>

**GeoIntel** is an advanced Python script that combines **real-time proxy fetching and verification** with **multi-source IP intelligence** and **optional reverse geocoding**. It ensures you get the data you need, even when direct requests fail.

---

## ✨ Key Features

* **🛡️ Proxy Resilience:** Automatically scrapes, deduplicates, and quickly verifies **hundreds of free proxies** from multiple sources using concurrent threads (fast TCP checks).
* **🔗 Smart Fallback:** Attempts direct requests first, but gracefully falls back to a **random, verified proxy** if a connection error, rate-limit (`429`/`402`), or general request failure occurs.
* **📍 Multi-Source Geolocation:** Gathers data from popular APIs like `ip-api.com` and `ipwho.is` for comprehensive coverage.
* **🗺️ Optional Reverse Geocode:** Uses **OpenCage** to turn coordinates into a detailed, human-readable address (requires API key).
* **🎨 Stunning Output:** Features a clean, professional, and easy-to-read console display powered by the **rich** library.

---

## 🚀 Getting Started

### Prerequisites

You need **Python 3.x** installed. Then, install the required packages:

```bash
pip install requests beautifulsoup4 rich tqdm
````

### Usage

1.  **Configure API Key (Optional):**
    To use the advanced **OpenCage Reverse Geocode** feature, you must update the API key within the script (`geointel_optimized.py`):

    ```python
    # geointel_optimized.py 
    OPENCAGE_API_KEY = "YOUR_OPENCAGE_KEY_HERE" # Replace with your actual key
    ```

2.  **Run the Tool:**

    ```bash
    python geointel_optimized.py
    ```

3.  **Input Target:**
    The script will first scrape and verify proxies. Once complete, it will prompt you:

    > **Enter target IP or hostname (leave empty to auto-detect your IP):**

      * Leave it **empty** to find the intelligence for **your current public IP**.
      * Enter any **IP address** or **hostname** (e.g., `google.com`).

-----

## ⚙️ Configuration (Inside the Script)

You can easily adjust the scraping and verification parameters:

| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `OPENCAGE_API_KEY` | Your OpenCage Geocoding API key for reverse lookup. | `7733d728...` |
| `PROXY_SOURCES` | List of URLs the script scrapes free proxies from. | 5 different URLs |
| `MAX_WORKERS` | Maximum concurrent threads for fast proxy verification. | `50` |

-----

## 💡 How It Works

1.  **Scrape & Verify:** Fetches proxies from defined sources and runs a **concurrent TCP connect check** to quickly filter out unusable connections.
2.  **Intelligent Request:** Attempts direct API calls. If the call fails (due to connection errors or API rate limits), it automatically retries the request using a random, working proxy from the verified list.
3.  **Data Aggregation:** Collects location and ASN/ISP data from multiple geolocation APIs.
4.  **Enrichment:** If geographic coordinates are available and the OpenCage key is set, it performs a **reverse geocode** lookup to provide detailed address information.

-----

## 📜 Licensing

This project is licensed under the **MIT License**.

-----

## 💜 Credits

Built with ❤️ by zanesense for open-source use. 

-----

**Get started with GeoIntel today and never get rate-limited again\!**
