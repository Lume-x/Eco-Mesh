# 🌐 EcoMesh — Decentralized, Solar-Powered Community Internet

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0%2B-darkgreen.svg)](https://www.djangoproject.com/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-CDN-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**EcoMesh** is a production-grade, venture-backed aesthetic Django web platform engineered for decentralized, 100% solar-powered Wi-Fi mesh networks in off-campus student quarters and underserved communities in Nigeria.

---

## ✨ Features

- ☀️ **Decentralized Solar Mesh Infrastructure:** Real-time telemetry monitoring for LiFePO4 battery levels, uptime SLA %, and maintenance scheduling.
- ⚡ **Perpetual Pay-As-You-Go Vouchers:** Non-expiring data bundles (₦100 for 1GB, ₦500 for 5GB, ₦1,000 for 10GB, ₦5,000 for 60GB). Megabytes never expire until consumed.
- 🔐 **Unique Captive Portal Wi-Fi Keys:** Auto-generated unique 8-character uppercase hex WPA3 keys for each student wallet.
- 🛠️ **Technician Booking Engine:** Interactive dispatch scheduler with automated conflict resolution preventing overlapping slots on the same node.
- 👑 **Superuser / Admin Consoles:**
  - **Live Node Infrastructure Manager:** Deploy new nodes, toggle operational modes (`ACTIVE`, `MAINTENANCE`, `OFFLINE`), set maintenance windows, and adjust battery charge.
  - **Promo Code Generator & Status Tracker:** Generate custom or bulk promo codes of any MB/GB amount and track redemption status in real time.
- 🎓 **UN SDG Alignment:** Aligned with **SDG 4** (*Quality Education*), **SDG 7** (*Affordable & Clean Energy*), and **SDG 9** (*Industry, Innovation & Infrastructure*).

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ecomesh.git
cd ecomesh
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations & Seed Database
```bash
python manage.py migrate
python manage.py seed_data
```

### 5. Start the Development Server
```bash
python manage.py runserver
```

Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 🧪 Running Automated Tests

Run the comprehensive unit and integration test suite:
```bash
python manage.py test
```

---

## 🏛️ System Architecture

- **Backend:** Python 3, Django MVT architecture, SQLite ORM, Built-in Session Auth, ModelForms.
- **Frontend:** Django Templates, Tailwind CSS (via CDN), Lucide Icons, AOS (Animate On Scroll).
- **Core Models:**
  - `MeshNode`: LiFePO4 battery health, operational status, maintenance windows, and uptime metrics.
  - `UserDataWallet`: Student data balance tracking and WPA3 Wi-Fi access keys.
  - `Voucher`: Scratch card code verification, redemption logging, and atomic balance crediting.
  - `ServiceSchedule`: Technician appointment booking with scheduling conflict validation.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
