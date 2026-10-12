# ⚡ EmergencyCharge AI

### Intelligent Laptop-to-Phone Emergency Charging Assistant

EmergencyCharge AI is a Python-based project designed to analyze laptop battery conditions and help users make safer, informed decisions during emergency phone charging.

## 🎯 Problem Statement

During emergencies, users may need to charge their phones using a laptop when a power bank or wall outlet is unavailable. However, laptop battery capacity and USB charging capabilities are limited.

## ✨ Key Features

- 🔋 Laptop battery status monitoring
- 🌡️ Battery and temperature safety checks, where supported
- ⚙️ Charging decision support: Approve, Warn, or Reject
- 📊 Energy calculations and battery analysis
- 💻 Windows-focused implementation
- 🔌 Android device integration through ADB, where configured

## 🛠️ Technology Stack

- Python
- FastAPI
- PySide6
- Windows device telemetry
- Android Debug Bridge (ADB)

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/raj9030-bit/EmergencyCharge-AI.git
cd EmergencyCharge-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate it on Windows

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

Check the project's source files and configuration for the correct entry point before launching the application.

## ⚠️ Important Limitations

- This software does not create additional electrical power.
- USB charging speed depends on the laptop's hardware, USB port, cable, and phone.
- Software alone cannot bypass physical USB power-delivery limits.
- Battery and temperature readings depend on available hardware telemetry.
- Safety recommendations do not replace hardware-level protection.

## 🔮 Future Improvements

- Improved device compatibility
- Better battery analytics
- User-friendly monitoring dashboard
- Expanded hardware testing

## 👨‍💻 Author

**Raj** — Computer Science Engineering Student

## 📜 License

A license has not yet been selected. All rights remain with the copyright holder unless otherwise specified.
