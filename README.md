# ✈ KVK FLIGHTS FLYZZ — Complete Booking System v3

## Quick Start

### 1. Install dependencies
```bash
pip install customtkinter mysql-connector-python reportlab pillow
```

### 2. Make sure MySQL is running
- Host: `localhost`
- User: `root`
- Password: `root`
- The database `kvk_flyzz` is **auto-created** on first run

### 3. Run
```bash
python main.py
```

---

## Default Admin Login
| Username | Password |
|----------|----------|
| `admin`  | `admin`  |

---

## Full Feature List

### Registration
- First Name, Last Name, Username, Password, Re-enter Password
- Password validation (min 6 chars, match check)

### Admin Panel
| Feature | Details |
|---------|---------|
| Dashboard | Live stats: active flights, users, bookings, total revenue |
| Add Flight | Flight Name, Number, Departure Area, Destination Area, Dep/Arr Time, Cost, Total Seats, Seats Booked (default 0), Luggage (default 30 kg) |
| Manage Flights | Full table view, remove flights |
| Passenger Records | All booked passengers with passport, contact, fare |
| Reports | Preview + CSV download of flight-wise summary |

### Booking Wizard (3 Steps)

**Step 1 — Seat Selection**
- Interactive 6-column grid (A–F rows)
- Window seats marked as `W` (e.g. `WA1`, `WA6`)
- 3 seats | aisle gap | 3 seats layout
- Green = available, Red = booked, Yellow = selected
- Auto-assign button available

**Step 2 — Passenger & Payment**
- First Name, Last Name
- Passport Number, Issue Country, Passport Expiry (validated — rejects expired)
- Email (format validated), Mobile (format validated)
- Baggage: 30 kg included free; extra baggage at **$8/kg**
- Live fare summary: Base Fare + Excess Baggage + 9% Tax = **Total Payable**
- T&C agreement checkbox required

**Step 3 — Confirmation**
- Boarding pass rendered on screen (tk.Canvas)
- PNR generated (6-character alphanumeric)
- **Download PDF** — professional landscape boarding pass via ReportLab
  - Shows: Route, Passenger, Flight, Seat, PNR, Fare, Luggage allowance
  - Footer warning: **"Boarding closes 1 hour before departure"**

### My Bookings
- Full history of all bookings for logged-in user
