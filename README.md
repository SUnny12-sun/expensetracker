# SpendWise - Modern Expense Tracker with Authentication & Database

SpendWise is a responsive, feature-rich multi-user Expense Tracker and Budget Manager. It features a persistent SQLite backend database with password authentication, multi-currency support (Default: **₹ INR**, with **$ USD**, **€ EUR**, **£ GBP**, **AED**, **C$ CAD**, **A$ AUD**, **¥ JPY**), 3+ months of rich historical data, dual weekly & monthly analytics, and 3-tier budget alerts.

---

## 🌟 Key Upgrades & Highlights

### 1. 🔐 User Authentication & Backend Database (`spendwise.db`)
- **Multi-User Isolation by Email:** Each email account has its own isolated expenses, budget configurations, and settings saved securely in SQLite.
- **Secure Password Hashing:** Uses PBKDF2-HMAC-SHA256 with cryptographic salt generation.
- **Sign Up / Sign In:** Beautiful modal dialog with instant 1-click test demo login (`demo@spendwise.app`).
- **Offline + Online Sync:** Works online with Flask REST API and caches locally so the application is fast and resilient.

### 2. 💱 Multi-Currency System (No More Dollar Lock-In!)
- **Dynamic Currency Formatter:** Format every card, daily average, chart tooltip, modal, and table in your preferred currency:
  - **₹ INR (Indian Rupee)** — default with comma localization (e.g. ₹12,500.00)
  - **$ USD (US Dollar)**
  - **€ EUR (Euro)**
  - **£ GBP (British Pound)**
  - **AED (UAE Dirham)**
  - **C$ CAD (Canadian Dollar)**
  - **A$ AUD (Australian Dollar)**
  - **¥ JPY (Japanese Yen)**
- **Header Currency Switcher:** Change currency anytime from the top bar dropdown or during signup.

### 3. 📊 Dual Tracking Views (Weekly & Monthly)
- **Weekly Tracking:** Mon–Sun breakdown with daily averages, day-over-day percentage changes, previous/next week navigation, and daily bar charts.
- **Monthly Tracking:** Weekly and category aggregates, Month-over-Month comparison with percentage delta and amount difference, plus 4-month historical trend comparison against budget caps.

### 4. 🎯 Budget Management with 3-Tier Dynamic Alerts
- 🟢 **Safe:** `< 75%` of budget cap
- 🟡 **Warning:** `75% – 90%` of budget cap
- 🔴 **Critical / Exceeded:** `> 90%` with prominent alert banners and over-budget indicators

### 5. 📜 3+ Months Rich Transaction History & Export
- Automatically generates **4 full months** of realistic data (rent/EMI, utilities, internet broadband, gym/streaming subscriptions, grocery hauls, dining out, and transit).
- Live search by note/tag, category, and payment method (UPI, Credit Card, Debit Card, Cash, Digital Wallet).
- Filter by Time Range (All Time, Past 3 Months, Last 30 Days, This Month, Last Month, Custom Range).
- **CSV Export & CSV Import** with currency headers.

---

## 🚀 How to Run

### Run Backend Server (Flask + SQLite Database)
In your terminal in this directory (`c:\Users\Dell\Downloads\expensetracker`):

```powershell
python server.py
```

Then open your browser at **[http://localhost:5000](http://localhost:5000)**.

---

## ⚡ Quick Test Credentials
- Click **"Sign In / Up"** in the top navigation bar.
- Click **"⚡ 1-Click Demo Login"** to immediately sign into `demo@spendwise.app` with preloaded 3+ months of rich historical expenses.
- Or click **"Create Account"** to register your own email and choose your preferred currency (e.g. ₹ INR, $ USD, € EUR, etc.).

---

## ⌨️ Keyboard Shortcuts
- `N`: Quick-add new expense
- `Esc`: Close any open modal
- `/`: Quick focus search bar on the History page
