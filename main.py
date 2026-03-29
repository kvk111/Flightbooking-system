"""
╔══════════════════════════════════════════════════════════════╗
║       KVK FLIGHTS FLYZZ — Enhanced Booking System v6         ║
║       Tkinter + MySQL + ReportLab PDF                         ║
╚══════════════════════════════════════════════════════════════╝

  pip install mysql-connector-python reportlab pillow

  MySQL: host=localhost | user=root | password=root
  DB auto-created on first run.
  Default Admin → username: admin | password: admin

  BOOKING WIZARD v6 — 5 DISTINCT PAGES:
  ─────────────────────────────────────────────────────────────
  Step 1 → Passenger Details  (name, passport, expiry, country)
  Step 2 → Contact Details    (email, mobile)
  Step 3 → Seat Selection     (airline seat map 3-3 layout)
  Step 4 → Meal Selection     (meal preference + baggage)
  Step 5 → Payment            (currency, summary FIXED at top, confirm)

  v6 changes: refactored/deduplicated code; Step 5 payment summary
              now rendered above the scrollable body (always visible).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
from mysql.connector import Error
import hashlib, random, string, re, os, math
from datetime import datetime, date, timedelta
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import HexColor

# ══════════════════════════════════════════════════════════════
#  COLOUR PALETTE
# ══════════════════════════════════════════════════════════════
BG       = "#0B0F1E"
PANEL    = "#111827"
CARD     = "#16213E"
INPUT_BG = "#1A2540"
BORDER   = "#1E3A5F"
ACCENT   = "#00B4D8"
ACCENT2  = "#0077B6"
SUCCESS  = "#00C896"
DANGER   = "#FF4560"
WARNING  = "#FFB703"
WHITE    = "#EAF0FF"
GREY     = "#7B93B4"
DARK_TEXT = "#0A0E1A"

FT  = ("Segoe UI", 28, "bold")
FH2 = ("Segoe UI", 16, "bold")
FH3 = ("Segoe UI", 12, "bold")
FB  = ("Segoe UI", 11)
FS  = ("Segoe UI",  9)
FM  = ("Consolas", 11)
FL  = ("Segoe UI", 10, "bold")

# ══════════════════════════════════════════════════════════════
#  CURRENCY CONFIG
# ══════════════════════════════════════════════════════════════
CURRENCIES = {
    "USD": {"symbol": "$",   "rate": 1.0,   "label": "USD – US Dollar"},
    "INR": {"symbol": "Rs.", "rate": 83.5,  "label": "INR – Indian Rupee"},
    "GBP": {"symbol": "GBP", "rate": 0.79,  "label": "GBP – British Pound"},
    "EUR": {"symbol": "EUR", "rate": 0.92,  "label": "EUR – Euro"},
    "AED": {"symbol": "AED", "rate": 3.67,  "label": "AED – UAE Dirham"},
    "SGD": {"symbol": "SGD", "rate": 1.35,  "label": "SGD – Singapore Dollar"},
    "AUD": {"symbol": "AUD", "rate": 1.53,  "label": "AUD – Australian Dollar"},
}

def fmt_currency(amount_usd, currency_code):
    cur = CURRENCIES.get(currency_code, CURRENCIES["USD"])
    return f"{cur['symbol']}{amount_usd * cur['rate']:,.2f}"

# ══════════════════════════════════════════════════════════════
#  IATA AIRPORT CODE DATABASE
# ══════════════════════════════════════════════════════════════
IATA_DB = {
    "MAA": ("Chennai International Airport", "Chennai", "India"),
    "BOM": ("Chhatrapati Shivaji Maharaj Intl", "Mumbai", "India"),
    "DEL": ("Indira Gandhi International", "New Delhi", "India"),
    "BLR": ("Kempegowda International", "Bengaluru", "India"),
    "HYD": ("Rajiv Gandhi International", "Hyderabad", "India"),
    "CCU": ("Netaji Subhas Chandra Bose Intl", "Kolkata", "India"),
    "COK": ("Cochin International", "Kochi", "India"),
    "AMD": ("Sardar Vallabhbhai Patel Intl", "Ahmedabad", "India"),
    "PNQ": ("Pune Airport", "Pune", "India"),
    "GAU": ("Lokpriya Gopinath Bordoloi Intl", "Guwahati", "India"),
    "TRV": ("Trivandrum International", "Thiruvananthapuram", "India"),
    "JAI": ("Jaipur International", "Jaipur", "India"),
    "LKO": ("Chaudhary Charan Singh Intl", "Lucknow", "India"),
    "ATQ": ("Sri Guru Ram Dass Jee Intl", "Amritsar", "India"),
    "DXB": ("Dubai International Airport", "Dubai", "United Arab Emirates"),
    "AUH": ("Abu Dhabi International", "Abu Dhabi", "United Arab Emirates"),
    "DOH": ("Hamad International Airport", "Doha", "Qatar"),
    "BAH": ("Bahrain International Airport", "Manama", "Bahrain"),
    "MCT": ("Muscat International Airport", "Muscat", "Oman"),
    "KWI": ("Kuwait International Airport", "Kuwait City", "Kuwait"),
    "RUH": ("King Khalid International", "Riyadh", "Saudi Arabia"),
    "JED": ("King Abdulaziz International", "Jeddah", "Saudi Arabia"),
    "TLV": ("Ben Gurion International", "Tel Aviv", "Israel"),
    "SIN": ("Singapore Changi Airport", "Singapore", "Singapore"),
    "KUL": ("Kuala Lumpur International", "Kuala Lumpur", "Malaysia"),
    "BKK": ("Suvarnabhumi Airport", "Bangkok", "Thailand"),
    "CGK": ("Soekarno-Hatta International", "Jakarta", "Indonesia"),
    "MNL": ("Ninoy Aquino International", "Manila", "Philippines"),
    "SGN": ("Tan Son Nhat International", "Ho Chi Minh City", "Vietnam"),
    "HAN": ("Noi Bai International", "Hanoi", "Vietnam"),
    "HKG": ("Hong Kong International", "Hong Kong", "China"),
    "PEK": ("Beijing Capital International", "Beijing", "China"),
    "PVG": ("Shanghai Pudong International", "Shanghai", "China"),
    "NRT": ("Narita International Airport", "Tokyo", "Japan"),
    "HND": ("Haneda Airport", "Tokyo", "Japan"),
    "ICN": ("Incheon International", "Seoul", "South Korea"),
    "LHR": ("Heathrow Airport", "London", "United Kingdom"),
    "LGW": ("Gatwick Airport", "London", "United Kingdom"),
    "CDG": ("Charles de Gaulle Airport", "Paris", "France"),
    "FRA": ("Frankfurt Airport", "Frankfurt", "Germany"),
    "AMS": ("Amsterdam Airport Schiphol", "Amsterdam", "Netherlands"),
    "MAD": ("Adolfo Suarez Madrid-Barajas", "Madrid", "Spain"),
    "FCO": ("Leonardo da Vinci Intl", "Rome", "Italy"),
    "ZRH": ("Zurich Airport", "Zurich", "Switzerland"),
    "IST": ("Istanbul Airport", "Istanbul", "Turkey"),
    "ATH": ("Athens International Airport", "Athens", "Greece"),
    "JFK": ("John F Kennedy International", "New York", "United States"),
    "LAX": ("Los Angeles International", "Los Angeles", "United States"),
    "ORD": ("O'Hare International Airport", "Chicago", "United States"),
    "ATL": ("Hartsfield-Jackson Atlanta Intl", "Atlanta", "United States"),
    "SFO": ("San Francisco International", "San Francisco", "United States"),
    "MIA": ("Miami International Airport", "Miami", "United States"),
    "YYZ": ("Toronto Pearson International", "Toronto", "Canada"),
    "GRU": ("Guarulhos International", "Sao Paulo", "Brazil"),
    "CAI": ("Cairo International Airport", "Cairo", "Egypt"),
    "JNB": ("O.R. Tambo International", "Johannesburg", "South Africa"),
    "NBO": ("Jomo Kenyatta International", "Nairobi", "Kenya"),
    "SYD": ("Sydney Kingsford Smith Intl", "Sydney", "Australia"),
    "MEL": ("Melbourne Airport", "Melbourne", "Australia"),
    "AKL": ("Auckland Airport", "Auckland", "New Zealand"),
}

def lookup_iata(code):
    return IATA_DB.get(code.upper().strip())

def search_iata(query):
    q = query.strip().upper()
    results = [
        (code, name, city, country)
        for code, (name, city, country) in IATA_DB.items()
        if q in code or q in city.upper() or q in name.upper() or q in country.upper()
    ]
    results.sort(key=lambda x: (0 if x[0].startswith(q) else 1, x[2]))
    return results[:8]

ALL_COUNTRIES = sorted([
    "Afghanistan","Albania","Algeria","Andorra","Angola","Antigua and Barbuda",
    "Argentina","Armenia","Australia","Austria","Azerbaijan","Bahamas","Bahrain",
    "Bangladesh","Barbados","Belarus","Belgium","Belize","Benin","Bhutan","Bolivia",
    "Bosnia and Herzegovina","Botswana","Brazil","Brunei","Bulgaria","Burkina Faso",
    "Burundi","Cabo Verde","Cambodia","Cameroon","Canada","Central African Republic",
    "Chad","Chile","China","Colombia","Comoros","Congo","Costa Rica","Croatia","Cuba",
    "Cyprus","Czech Republic","Denmark","Djibouti","Dominica","Dominican Republic",
    "Ecuador","Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia","Eswatini",
    "Ethiopia","Fiji","Finland","France","Gabon","Gambia","Georgia","Germany","Ghana",
    "Greece","Grenada","Guatemala","Guinea","Guinea-Bissau","Guyana","Haiti","Honduras",
    "Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland","Israel","Italy",
    "Jamaica","Japan","Jordan","Kazakhstan","Kenya","Kiribati","Kuwait","Kyrgyzstan",
    "Laos","Latvia","Lebanon","Lesotho","Liberia","Libya","Liechtenstein","Lithuania",
    "Luxembourg","Madagascar","Malawi","Malaysia","Maldives","Mali","Malta",
    "Marshall Islands","Mauritania","Mauritius","Mexico","Micronesia","Moldova",
    "Monaco","Mongolia","Montenegro","Morocco","Mozambique","Myanmar","Namibia","Nauru",
    "Nepal","Netherlands","New Zealand","Nicaragua","Niger","Nigeria","North Korea",
    "North Macedonia","Norway","Oman","Pakistan","Palau","Palestine","Panama",
    "Papua New Guinea","Paraguay","Peru","Philippines","Poland","Portugal","Qatar",
    "Romania","Russia","Rwanda","Saint Kitts and Nevis","Saint Lucia",
    "Saint Vincent and the Grenadines","Samoa","San Marino","Sao Tome and Principe",
    "Saudi Arabia","Senegal","Serbia","Seychelles","Sierra Leone","Singapore",
    "Slovakia","Slovenia","Solomon Islands","Somalia","South Africa","South Korea",
    "South Sudan","Spain","Sri Lanka","Sudan","Suriname","Sweden","Switzerland","Syria",
    "Taiwan","Tajikistan","Tanzania","Thailand","Timor-Leste","Togo","Tonga",
    "Trinidad and Tobago","Tunisia","Turkey","Turkmenistan","Tuvalu","Uganda","Ukraine",
    "United Arab Emirates","United Kingdom","United States","Uruguay","Uzbekistan",
    "Vanuatu","Vatican City","Venezuela","Vietnam","Yemen","Zambia","Zimbabwe",
])

# ══════════════════════════════════════════════════════════════
#  DATABASE HELPERS
# ══════════════════════════════════════════════════════════════
def _conn():
    return mysql.connector.connect(
        host="localhost", user="root", password="root", database="kvk_flyzz")

def _sha(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def _pnr():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

def setup_db():
    raw = mysql.connector.connect(host="localhost", user="root", password="root")
    c = raw.cursor()
    c.execute("CREATE DATABASE IF NOT EXISTS kvk_flyzz")
    c.execute("USE kvk_flyzz")
    c.execute("""CREATE TABLE IF NOT EXISTS admins(
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(64) NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(60) NOT NULL,
        last_name VARCHAR(60) NOT NULL,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(64) NOT NULL,
        is_deleted TINYINT(1) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    try: c.execute("ALTER TABLE users ADD COLUMN is_deleted TINYINT(1) DEFAULT 0")
    except: pass
    c.execute("""CREATE TABLE IF NOT EXISTS flights(
        id INT AUTO_INCREMENT PRIMARY KEY,
        flight_name VARCHAR(100) NOT NULL,
        flight_number VARCHAR(20) UNIQUE NOT NULL,
        departure_area VARCHAR(100) NOT NULL,
        destination_area VARCHAR(100) NOT NULL,
        departure_iata VARCHAR(10) DEFAULT '',
        destination_iata VARCHAR(10) DEFAULT '',
        departure_time DATETIME NOT NULL,
        arrival_time DATETIME NOT NULL,
        ticket_cost DECIMAL(10,2) NOT NULL,
        total_seats INT NOT NULL DEFAULT 180,
        seats_booked INT NOT NULL DEFAULT 0,
        luggage_kg INT NOT NULL DEFAULT 30,
        status ENUM('active','cancelled') DEFAULT 'active',
        is_deleted TINYINT(1) DEFAULT 0,
        image_path VARCHAR(500) DEFAULT NULL)""")
    for col_def in [
        "ADD COLUMN image_path VARCHAR(500) DEFAULT NULL",
        "ADD COLUMN is_deleted TINYINT(1) DEFAULT 0",
        "ADD COLUMN departure_iata VARCHAR(10) DEFAULT ''",
        "ADD COLUMN destination_iata VARCHAR(10) DEFAULT ''",
    ]:
        try: c.execute(f"ALTER TABLE flights {col_def}")
        except: pass
    c.execute("""CREATE TABLE IF NOT EXISTS bookings(
        id INT AUTO_INCREMENT PRIMARY KEY,
        pnr VARCHAR(8) UNIQUE NOT NULL,
        user_id INT NOT NULL,
        flight_id INT NOT NULL,
        seat VARCHAR(6) NOT NULL,
        pax_first_name VARCHAR(60) NOT NULL,
        pax_last_name VARCHAR(60) NOT NULL,
        passport_no VARCHAR(20) NOT NULL,
        passport_expiry DATE NOT NULL,
        issue_country VARCHAR(80) NOT NULL,
        email VARCHAR(100) NOT NULL,
        mobile VARCHAR(20) NOT NULL,
        meal_pref VARCHAR(30) DEFAULT 'No Select',
        base_fare DECIMAL(10,2) NOT NULL,
        excess_baggage_kg INT NOT NULL DEFAULT 0,
        excess_baggage_cost DECIMAL(10,2) NOT NULL DEFAULT 0,
        total_paid DECIMAL(10,2) NOT NULL,
        currency_code VARCHAR(5) DEFAULT 'USD',
        is_deleted TINYINT(1) DEFAULT 0,
        booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(flight_id) REFERENCES flights(id))""")
    for col_def in [
        "ADD COLUMN currency_code VARCHAR(5) DEFAULT 'USD'",
        "ADD COLUMN is_deleted TINYINT(1) DEFAULT 0",
        "ADD COLUMN meal_pref VARCHAR(30) DEFAULT 'No Select'",
    ]:
        try: c.execute(f"ALTER TABLE bookings {col_def}")
        except: pass
    c.execute("INSERT IGNORE INTO admins(username,password_hash) VALUES(%s,%s)",
              ("admin", _sha("admin")))
    raw.commit(); raw.close()

# ══════════════════════════════════════════════════════════════
#  UTILITIES
# ══════════════════════════════════════════════════════════════
def _duration_str(dep_dt, arr_dt):
    total_min = int((arr_dt - dep_dt).total_seconds() // 60)
    h, m = divmod(total_min, 60)
    return f"{h}h {m:02d}m"

def _draw_qr_on_canvas(c, data, x, y, size):
    import hashlib as _h
    bits = bin(int(_h.md5(data.encode()).hexdigest(), 16))[2:].zfill(128)
    N, cell = 11, size / 13
    bx, by = x, y - size
    c.setFillColor(colors.white); c.rect(bx, by, size, size, fill=1, stroke=0)
    c.setFillColor(colors.black)
    for row in range(N):
        for col in range(N):
            if bits[(row * N + col) % 128] == '1':
                c.rect(bx+(col+1)*cell, by+(N-row)*cell, cell*.85, cell*.85, fill=1, stroke=0)
    for fx, fy in [(bx+cell*.5, by+size-cell*3.5),
                   (bx+size-cell*3.5, by+size-cell*3.5),
                   (bx+cell*.5, by+cell*.5)]:
        c.setFillColor(colors.black); c.rect(fx, fy, cell*3, cell*3, fill=1, stroke=0)
        c.setFillColor(colors.white); c.rect(fx+cell*.4, fy+cell*.4, cell*2.2, cell*2.2, fill=1, stroke=0)
        c.setFillColor(colors.black); c.rect(fx+cell*.8, fy+cell*.8, cell*1.4, cell*1.4, fill=1, stroke=0)
    c.setFillColor(colors.black)

# ══════════════════════════════════════════════════════════════
#  WIDGET HELPERS
# ══════════════════════════════════════════════════════════════
def _style_ttk():
    s = ttk.Style(); s.theme_use("clam")
    s.configure("KVK.Treeview", background=CARD, foreground=WHITE, rowheight=28,
                fieldbackground=CARD, borderwidth=0, font=FB)
    s.configure("KVK.Treeview.Heading", background=INPUT_BG, foreground=ACCENT,
                font=("Segoe UI", 11, "bold"), relief="flat")
    s.map("KVK.Treeview", background=[("selected", INPUT_BG)])
    s.configure("KVK.Vertical.TScrollbar", background=BORDER,
                troughcolor=PANEL, arrowcolor=GREY)

def lbl(parent, text, font=FB, fg=WHITE, bg=None, anchor="w", **kw):
    return tk.Label(parent, text=text, font=font, fg=fg,
                    bg=bg or parent["bg"], anchor=anchor, **kw)

def entry_w(parent, width=26, show=None):
    kw = dict(bg=INPUT_BG, fg=WHITE, insertbackground=ACCENT, relief="flat",
              font=FB, width=width, highlightthickness=1,
              highlightbackground=BORDER, highlightcolor=ACCENT)
    if show: kw["show"] = show
    return tk.Entry(parent, **kw)

def btn_w(parent, text, cmd, bg=ACCENT2, fg=WHITE, w=18, font=FL):
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, font=font,
                     relief="flat", cursor="hand2", width=w,
                     activebackground=ACCENT, activeforeground=DARK_TEXT, padx=8, pady=6)

def card_f(parent, bg=CARD, **kw):
    return tk.Frame(parent, bg=bg, relief="flat",
                    highlightthickness=1, highlightbackground=BORDER, **kw)

def make_tree(parent, cols, widths, height=12):
    f = tk.Frame(parent, bg=BG); f.pack(fill="both", expand=True)
    tree = ttk.Treeview(f, columns=cols, show="headings",
                        style="KVK.Treeview", height=height)
    for col, w in zip(cols, widths):
        tree.heading(col, text=col); tree.column(col, anchor="center", width=w, minwidth=w)
    vsb = ttk.Scrollbar(f, orient="vertical", command=tree.yview, style="KVK.Vertical.TScrollbar")
    hsb = ttk.Scrollbar(f, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew"); vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    f.grid_rowconfigure(0, weight=1); f.grid_columnconfigure(0, weight=1)
    return tree, f

def build_sidebar_layout(root, nav_items, logout_cmd, user_label=""):
    for w in root.winfo_children(): w.destroy()
    outer = tk.Frame(root, bg=BG); outer.pack(fill="both", expand=True)
    side = tk.Frame(outer, bg=PANEL, width=210); side.pack(side="left", fill="y")
    side.pack_propagate(False)
    logo_f = tk.Frame(side, bg=PANEL); logo_f.pack(pady=(24, 6), padx=16)
    tk.Label(logo_f, text="✈", font=("Segoe UI", 36), bg=PANEL, fg=ACCENT).pack()
    tk.Label(logo_f, text="KVK FLYZZ", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=WHITE).pack()
    if user_label:
        tk.Label(logo_f, text=user_label, font=FS, bg=PANEL, fg=ACCENT).pack(pady=2)
    tk.Frame(side, bg=BORDER, height=1).pack(fill="x", padx=16, pady=6)
    for icon_txt, cmd in nav_items:
        tk.Button(side, text=icon_txt, command=cmd, bg=PANEL, fg=GREY, font=FB,
                  relief="flat", anchor="w", padx=20, pady=10, cursor="hand2",
                  activebackground=INPUT_BG, activeforeground=ACCENT, width=24).pack(fill="x")
    tk.Button(side, text="🚪  Logout", command=logout_cmd, bg=PANEL, fg=DANGER, font=FB,
              relief="flat", anchor="w", padx=20, pady=10, cursor="hand2",
              activebackground="#2A0A10", activeforeground=DANGER, width=24
              ).pack(side="bottom", fill="x", pady=(0, 16))
    content = tk.Frame(outer, bg=BG); content.pack(side="right", fill="both", expand=True)
    return side, content

def page_header(content, title, sub=""):
    f = tk.Frame(content, bg=BG); f.pack(fill="x", padx=32, pady=(20, 4))
    lbl(f, title, FT, WHITE, BG).pack(anchor="w")
    if sub: lbl(f, sub, FB, GREY, BG).pack(anchor="w", pady=(2, 0))
    tk.Frame(content, bg=BORDER, height=1).pack(fill="x", padx=32, pady=(4, 8))

def clear_content(content):
    for w in content.winfo_children(): w.destroy()

def draw_step_bar(parent, current_step, steps):
    bar_f = tk.Frame(parent, bg=BG); bar_f.pack(fill="x", padx=32, pady=(0, 10))
    for i, label_text in enumerate(steps):
        step_num = i + 1
        col = tk.Frame(bar_f, bg=BG); col.pack(side="left", expand=True, fill="x")
        circle_bg = ACCENT2 if step_num < current_step else (ACCENT if step_num == current_step else INPUT_BG)
        circle_fg = WHITE if step_num <= current_step else GREY
        tk.Label(col, text="✓" if step_num < current_step else str(step_num),
                 font=("Segoe UI", 10, "bold"), bg=circle_bg, fg=circle_fg,
                 width=3, relief="flat", highlightthickness=2,
                 highlightbackground=ACCENT if step_num == current_step else BORDER).pack()
        tk.Label(col, text=label_text, font=FS, bg=BG,
                 fg=ACCENT if step_num == current_step else (SUCCESS if step_num < current_step else GREY),
                 wraplength=90, justify="center").pack()
        if i < len(steps) - 1:
            tk.Frame(bar_f, bg=ACCENT2 if step_num < current_step else BORDER,
                     height=2, width=24).pack(side="left", pady=10)

def make_scrollable(parent):
    """Return a scrollable inner frame packed into parent."""
    outer = tk.Frame(parent, bg=BG); outer.pack(fill="both", expand=True)
    canvas_s = tk.Canvas(outer, bg=BG, highlightthickness=0)
    vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas_s.yview,
                        style="KVK.Vertical.TScrollbar")
    canvas_s.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y"); canvas_s.pack(side="left", fill="both", expand=True)
    scroll_f = tk.Frame(canvas_s, bg=BG)
    win_id = canvas_s.create_window((0, 0), window=scroll_f, anchor="nw")
    canvas_s.bind("<Configure>", lambda e: canvas_s.itemconfig(win_id, width=e.width))
    scroll_f.bind("<Configure>", lambda e: canvas_s.configure(scrollregion=canvas_s.bbox("all")))
    def _wheel(e): canvas_s.yview_scroll(int(-1*(e.delta/120)), "units")
    def _bind(e): canvas_s.bind_all("<MouseWheel>", _wheel)
    def _unbind(e): canvas_s.unbind_all("<MouseWheel>")
    canvas_s.bind("<Enter>", _bind); canvas_s.bind("<Leave>", _unbind)
    scroll_f.bind("<Enter>", _bind); scroll_f.bind("<Leave>", _unbind)
    return scroll_f

def open_calendar(date_var):
    """Open a date-picker popup and write the picked date into date_var."""
    cal = tk.Toplevel(); cal.title("Pick Date")
    cal.configure(bg=PANEL); cal.resizable(False, False); cal.grab_set()
    import calendar
    try: ref = datetime.strptime(date_var.get(), "%Y-%m-%d")
    except: ref = datetime.today()
    cy = tk.IntVar(value=ref.year); cm = tk.IntVar(value=ref.month)
    nav = tk.Frame(cal, bg=PANEL); nav.pack(fill="x", padx=8, pady=(8, 2))
    mlbl = tk.Label(nav, text="", font=FL, bg=PANEL, fg=WHITE); mlbl.pack(side="left", expand=True)
    days_f = tk.Frame(cal, bg=PANEL); days_f.pack(padx=8, pady=4)

    def _render():
        for w in days_f.winfo_children(): w.destroy()
        y, m = cy.get(), cm.get()
        mlbl.config(text=f"{calendar.month_name[m]}  {y}")
        for ci, dh in enumerate(["Mo","Tu","We","Th","Fr","Sa","Su"]):
            tk.Label(days_f, text=dh, font=FS, bg=PANEL, fg=GREY, width=4
                     ).grid(row=0, column=ci, padx=1, pady=1)
        for ri, week in enumerate(calendar.monthcalendar(y, m)):
            for ci, day in enumerate(week):
                if day == 0:
                    tk.Label(days_f, text="", bg=PANEL, width=4).grid(row=ri+1, column=ci, padx=1, pady=1)
                else:
                    is_t = (y == datetime.today().year and m == datetime.today().month
                            and day == datetime.today().day)
                    tk.Button(days_f, text=str(day), font=FS,
                              bg=ACCENT2 if is_t else INPUT_BG, fg=WHITE,
                              relief="flat", width=4, cursor="hand2",
                              command=lambda d=day: _pick(y, m, d)
                              ).grid(row=ri+1, column=ci, padx=1, pady=1)

    def _pick(y, m, d): date_var.set(f"{y:04d}-{m:02d}-{d:02d}"); cal.destroy()
    def _prev():
        m = cm.get() - 1
        if m < 1: m = 12; cy.set(cy.get() - 1)
        cm.set(m); _render()
    def _next():
        m = cm.get() + 1
        if m > 12: m = 1; cy.set(cy.get() + 1)
        cm.set(m); _render()
    tk.Button(nav, text="◀", command=_prev, bg=PANEL, fg=ACCENT, font=FL, relief="flat", cursor="hand2").pack(side="left")
    tk.Button(nav, text="▶", command=_next, bg=PANEL, fg=ACCENT, font=FL, relief="flat", cursor="hand2").pack(side="right")
    _render()

def make_calendar_picker(parent, label_text, initial_value="", bg=CARD):
    frame = tk.Frame(parent, bg=bg)
    lbl(frame, label_text, FL, GREY, bg).pack(anchor="w")
    row = tk.Frame(frame, bg=bg); row.pack(anchor="w")
    _var = tk.StringVar(value=initial_value)
    tk.Label(row, textvariable=_var, bg=INPUT_BG, fg=WHITE, font=FB, width=14,
             anchor="w", padx=6, highlightthickness=1, highlightbackground=BORDER
             ).pack(side="left", ipady=5)
    tk.Button(row, text="📅", command=lambda: open_calendar(_var),
              bg=ACCENT2, fg=WHITE, font=FB, relief="flat", cursor="hand2",
              padx=8, pady=4).pack(side="left", padx=(6, 0))

    class _Proxy:
        def get(self): return _var.get()
        def set(self, v): _var.set(v)
    return frame, _Proxy()

# ══════════════════════════════════════════════════════════════
#  IATA AUTOCOMPLETE ENTRY
# ══════════════════════════════════════════════════════════════
class IATAEntry(tk.Frame):
    def __init__(self, parent, bg=BG, width=10, on_select=None, **kw):
        super().__init__(parent, bg=bg, **kw)
        self._on_select = on_select; self._popup = None; self._suppress = False
        self._var = tk.StringVar()
        self._entry = tk.Entry(self, textvariable=self._var, bg=INPUT_BG, fg=WHITE,
                               insertbackground=ACCENT, relief="flat",
                               font=("Segoe UI", 11, "bold"), width=width,
                               highlightthickness=1, highlightbackground=BORDER,
                               highlightcolor=ACCENT)
        self._entry.pack(side="left")
        self._info_lbl = tk.Label(self, text="", font=FS, bg=bg, fg=ACCENT,
                                   anchor="w", wraplength=220)
        self._info_lbl.pack(side="left", padx=(6, 0))
        self._var.trace("w", self._on_type)
        self._entry.bind("<FocusOut>", self._on_focusout)
        self._entry.bind("<Escape>", lambda e: self._close_popup())
        self._entry.bind("<Down>", self._focus_popup)
        self._entry.bind("<Return>", self._on_return)

    def _on_type(self, *args):
        if self._suppress: return
        q = self._var.get().strip()
        if len(q) < 2: self._close_popup(); self._info_lbl.config(text=""); return
        results = search_iata(q)
        if results: self._show_popup(results)
        else:
            self._close_popup()
            if len(q) >= 3: self._info_lbl.config(text="⚠ No match", fg=WARNING)

    def _show_popup(self, results):
        self._close_popup()
        popup = tk.Toplevel(self.winfo_toplevel())
        popup.wm_overrideredirect(True); popup.configure(bg=PANEL); popup.attributes("-topmost", True)
        self._entry.update_idletasks()
        x = self._entry.winfo_rootx(); y = self._entry.winfo_rooty() + self._entry.winfo_height() + 2
        popup.geometry(f"+{x}+{y}")
        listbox = tk.Listbox(popup, bg=CARD, fg=WHITE, font=("Consolas", 10),
                              selectbackground=ACCENT2, selectforeground=WHITE,
                              relief="flat", highlightthickness=1, highlightbackground=BORDER,
                              height=min(len(results), 7), width=52, activestyle="dotbox")
        listbox.pack(fill="both", expand=True, padx=1, pady=1)
        self._popup_data = []
        for code, name, city, country in results:
            listbox.insert("end", f"  {code}   {city}, {country}  —  {name[:32]}")
            self._popup_data.append((code, name, city, country))

        def _select(event=None):
            sel = listbox.curselection()
            if sel:
                code, name, city, country = self._popup_data[sel[0]]
                self._suppress = True; self._var.set(code); self._suppress = False
                self._info_lbl.config(text=f"✓ {city}, {country}  |  {name[:30]}", fg=SUCCESS)
                if self._on_select: self._on_select(code, name, city, country)
                self._close_popup(); self._entry.focus_set()

        listbox.bind("<Double-Button-1>", _select); listbox.bind("<Return>", _select)
        listbox.bind("<Escape>", lambda e: self._close_popup()); listbox.bind("<Tab>", _select)
        self._entry.bind("<Down>", lambda e: (listbox.selection_set(0), listbox.focus_set()))
        self._popup = popup; self._listbox = listbox

    def _focus_popup(self, event=None):
        if self._popup and hasattr(self, '_listbox'):
            self._listbox.selection_set(0); self._listbox.focus_set()

    def _on_return(self, event=None):
        q = self._var.get().strip().upper(); r = lookup_iata(q)
        if r:
            self._info_lbl.config(text=f"✓ {r[1]}, {r[2]}", fg=SUCCESS)
            if self._on_select: self._on_select(q, r[0], r[1], r[2])
        self._close_popup()

    def _on_focusout(self, event=None):
        self.after(200, self._close_popup)
        q = self._var.get().strip().upper()
        if len(q) == 3:
            r = lookup_iata(q)
            if r: self._info_lbl.config(text=f"✓ {r[1]}, {r[2]}", fg=SUCCESS)
            elif q: self._info_lbl.config(text="⚠ Unknown code", fg=WARNING)

    def _close_popup(self):
        if self._popup:
            try: self._popup.destroy()
            except: pass
            self._popup = None

    def get(self): return self._var.get().strip().upper()
    def set(self, v):
        self._suppress = True; self._var.set(v); self._suppress = False
        r = lookup_iata(v)
        if r: self._info_lbl.config(text=f"✓ {r[1]}, {r[2]}", fg=SUCCESS)

# ══════════════════════════════════════════════════════════════
#  COUNTRY DROPDOWN WITH SEARCH
# ══════════════════════════════════════════════════════════════
class CountryPicker(tk.Frame):
    def __init__(self, parent, bg=CARD, **kw):
        super().__init__(parent, bg=bg, **kw)
        self._var = tk.StringVar()
        self._entry = tk.Entry(self, textvariable=self._var, bg=INPUT_BG, fg=WHITE,
                               insertbackground=ACCENT, relief="flat", font=FB, width=28,
                               highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT)
        self._entry.pack(side="left")
        tk.Button(self, text="▼", command=self._open_picker, bg=ACCENT2, fg=WHITE,
                  font=FS, relief="flat", cursor="hand2", padx=6, pady=4
                  ).pack(side="left", padx=(4, 0))

    def _open_picker(self):
        win = tk.Toplevel(); win.title("Select Country")
        win.configure(bg=PANEL); win.grab_set(); win.geometry("340x460")
        sf = tk.Frame(win, bg=PANEL); sf.pack(fill="x", padx=10, pady=8)
        lbl(sf, "Search:", FL, GREY, PANEL).pack(side="left")
        sv = tk.StringVar()
        se = tk.Entry(sf, textvariable=sv, bg=INPUT_BG, fg=WHITE, insertbackground=ACCENT,
                      relief="flat", font=FB, width=22, highlightthickness=1,
                      highlightbackground=BORDER)
        se.pack(side="left", padx=6); se.focus()
        listbox = tk.Listbox(win, bg=CARD, fg=WHITE, font=FB, selectbackground=ACCENT2,
                             selectforeground=WHITE, relief="flat", highlightthickness=0, height=18)
        sb = ttk.Scrollbar(win, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=sb.set)
        listbox.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=4)
        sb.pack(side="right", fill="y", pady=4)

        def _refresh(*args):
            q = sv.get().strip().lower(); listbox.delete(0, "end")
            for c in ALL_COUNTRIES:
                if q in c.lower(): listbox.insert("end", c)
        sv.trace("w", _refresh); _refresh()

        def _select(event=None):
            sel = listbox.curselection()
            if sel: self._var.set(listbox.get(sel[0])); win.destroy()
        listbox.bind("<Double-Button-1>", _select); listbox.bind("<Return>", _select)
        tk.Button(win, text="Select", command=_select, bg=SUCCESS, fg=DARK_TEXT,
                  font=FL, relief="flat", cursor="hand2").pack(pady=6)

    def get(self): return self._var.get().strip()
    def set(self, v): self._var.set(v)

# ══════════════════════════════════════════════════════════════
#  IMPORTANT INFORMATION TEXT
# ══════════════════════════════════════════════════════════════
IMPORTANT_INFO = """CHECK-IN & ARRIVAL
• Arrive at airport at least 4 hours before departure.
• Check-in counters close 120 minutes before scheduled departure.
• Carry valid passport (at least 6 months validity) and all required visas.
• Present your e-ticket on mobile/tablet or printed copy at airport entry.

TRAVEL REQUIREMENTS
• Verify all travel documents including visas and transit visas per your nationality.
• Tourist visa holders must carry a return ticket to board.
• KVK Flyzz is not liable for insufficient documentation or missed connections.

CANCELLATION POLICY
• Cancellations allowed up to 24 hours before departure via your KVK Flyzz account.
• Within 24 hours of departure, contact the airline or KVK Flyzz Customer Service.
• KVK Flyzz cancellation fee: Rs.649 per traveller per sector (airline charges additional).
• Refund requests must be submitted within 90 days of travel date.
• No partial cancellation for layover or connecting flight bookings.

BAGGAGE POLICY
• Checked Baggage: As per your ticket (included in fare).
• Hand/Cabin Baggage: 7 kg per passenger (standard across all KVK Flyzz flights).
• Excess baggage charged at USD 8 per kg — pre-purchase recommended.
• Adhere to airline baggage dimension guidelines to avoid additional charges.

MEALS
• Complimentary meal is included on all KVK Flyzz flights.
• Special meal preferences can be pre-selected (vegetarian, vegan, halal, etc.).
• If no selection is made, standard complimentary meal will be served.

────────────────────────────────────────────────
Contact: 1800005256  |  Email: KVKFLYZZ@gmail.com
THANKS FOR CHOOSING KVK FLYZZ ✈
────────────────────────────────────────────────"""

# ══════════════════════════════════════════════════════════════
#  PDF TICKET GENERATOR
# ══════════════════════════════════════════════════════════════
def generate_pdf_ticket(td: dict, save_path: str):
    W, H = landscape(A4)
    c = rl_canvas.Canvas(save_path, pagesize=(W, H))
    _draw_boarding_pass_page(c, td, W, H)
    c.showPage()
    _draw_info_page(c, td, W, H)
    c.save()

def _draw_boarding_pass_page(c, td, W, H):
    PAD = 18*mm; BP_W = W-2*PAD; BP_H = H-2*PAD; BP_X = PAD; BP_Y = PAD
    c.setFillColor(HexColor("#EEF2F7")); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#C8D0DC")); c.roundRect(BP_X+3, BP_Y-3, BP_W, BP_H, 10*mm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.roundRect(BP_X, BP_Y, BP_W, BP_H, 10*mm, fill=1, stroke=0)
    HDR_H = 22*mm
    c.setFillColor(HexColor("#0A2647")); c.roundRect(BP_X, BP_Y+BP_H-HDR_H, BP_W, HDR_H, 10*mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#0A2647")); c.rect(BP_X, BP_Y+BP_H-HDR_H, BP_W, HDR_H/2, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 16)
    c.drawString(BP_X+10*mm, BP_Y+BP_H-14*mm, "✈  KVK FLIGHTS FLYZZ")
    c.setFont("Helvetica", 9); c.setFillColor(HexColor("#90CAF9"))
    c.drawRightString(BP_X+BP_W-10*mm, BP_Y+BP_H-14*mm, "NON-STOP  |  ECONOMY CLASS  |  BOARDING PASS")
    STUB_W = 58*mm; stub_x = BP_X+BP_W-STUB_W
    c.setStrokeColor(HexColor("#BBCCDD")); c.setDash([3, 4])
    c.line(stub_x, BP_Y+4*mm, stub_x, BP_Y+BP_H-HDR_H-1*mm); c.setDash([])
    c.setFillColor(HexColor("#AABBCC")); c.setFont("Helvetica", 11)
    c.drawString(stub_x-3*mm, BP_Y+BP_H//2-4*mm, "✂")
    MAIN_X = BP_X+8*mm; MAIN_W = stub_x-BP_X-14*mm; TOP_Y = BP_Y+BP_H-HDR_H-8*mm
    dep_code = td.get("dep_iata", td["departure"][:3]).upper()
    arr_code = td.get("arr_iata", td["destination"][:3]).upper()
    c.setFillColor(HexColor("#0A2647")); c.setFont("Helvetica-Bold", 44)
    c.drawString(MAIN_X, TOP_Y-16*mm, dep_code)
    dur_x = MAIN_X+40*mm
    c.setFont("Helvetica", 8); c.setFillColor(HexColor("#888"))
    c.drawCentredString(dur_x+12*mm, TOP_Y-5*mm, td.get("duration", ""))
    c.setStrokeColor(HexColor("#0077B6")); c.setLineWidth(1.5)
    c.line(dur_x, TOP_Y-11*mm, dur_x+24*mm, TOP_Y-11*mm)
    c.setFillColor(HexColor("#0077B6")); c.setFont("Helvetica-Bold", 16)
    c.drawString(dur_x+22*mm, TOP_Y-14*mm, "→")
    c.setFillColor(HexColor("#0A2647")); c.setFont("Helvetica-Bold", 44)
    c.drawString(dur_x+28*mm, TOP_Y-16*mm, arr_code)
    c.setFont("Helvetica", 8); c.setFillColor(HexColor("#555"))
    c.drawString(MAIN_X, TOP_Y-21*mm, td["departure"])
    c.drawString(dur_x+28*mm, TOP_Y-21*mm, td["destination"])
    c.setFillColor(HexColor("#E8F4FB"))
    c.roundRect(MAIN_X, TOP_Y-28*mm, 28*mm, 6*mm, 2*mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#0077B6")); c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(MAIN_X+14*mm, TOP_Y-25.5*mm, "NON-STOP")
    Y_INFO = TOP_Y-34*mm
    col_data = [
        [("PASSENGER NAME", td["pax_name"]), ("FLIGHT", td["flight_number"]), ("DATE OF TRAVEL", td["dep_time"][:11])],
        [("DEPARTURE", td["dep_time"]), ("ARRIVAL", td["arr_time"]), ("TRAVEL DURATION", td.get("duration","—"))],
        [("PASSPORT NO.", td["passport"]), ("ISSUE COUNTRY", td["issue_country"]), ("PASSPORT EXPIRY", td.get("passport_exp","—"))],
        [("EMAIL", td["email"][:24]), ("MOBILE", td["mobile"]), ("BOOKED ON", td.get("booked_date","—"))],
    ]
    for ci, col_fields in enumerate(col_data):
        cx = MAIN_X+ci*(MAIN_W/4)
        for ri, (lbl_t, val) in enumerate(col_fields):
            ry = Y_INFO-ri*13*mm
            c.setFont("Helvetica", 6.5); c.setFillColor(HexColor("#999")); c.drawString(cx, ry, lbl_t)
            c.setFont("Helvetica-Bold", 8.5); c.setFillColor(HexColor("#1A2A4A")); c.drawString(cx, ry-4.5*mm, str(val))
    sep_y = BP_Y+22*mm; c.setStrokeColor(HexColor("#DDE4EE")); c.setLineWidth(0.5)
    c.line(MAIN_X, sep_y, stub_x-6*mm, sep_y)
    fare_y = BP_Y+12*mm; cur_code = td.get("currency_code","USD")
    items = [
        ("BASE FARE",    fmt_currency(td["base_fare"], cur_code)),
        ("EXC. BAGGAGE", fmt_currency(td["excess_cost"], cur_code) if td["excess_kg"] else "Incl."),
        ("TOTAL PAID",   fmt_currency(td["total_paid"], cur_code)+f" ({cur_code})"),
        ("CHECKED BAG",  f"{td['luggage_kg']} kg"),
        ("HAND LUGGAGE", "7 kg"),
        ("MEAL",         td.get("meal_pref","Complimentary")),
        ("DEP TERMINAL", "Terminal 1"),
        ("ARR TERMINAL", "Terminal 2"),
    ]
    item_w = MAIN_W/len(items)
    for i, (lbl_t, val) in enumerate(items):
        ix = MAIN_X+i*item_w
        c.setFont("Helvetica", 6); c.setFillColor(HexColor("#999")); c.drawString(ix, fare_y+6*mm, lbl_t)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(HexColor("#0A2647") if "TOTAL" in lbl_t else HexColor("#333"))
        c.drawString(ix, fare_y, val)
    c.setFont("Helvetica-Oblique", 7); c.setFillColor(HexColor("#AAA"))
    c.drawString(MAIN_X, BP_Y+4*mm,
                 f"Ticket Purchased: {td.get('booked_date','—')}   |   "
                 f"Boarding closes 60 min before: {td.get('boarding_closes','—')}")
    stub_mid = stub_x+STUB_W/2; stub_top = BP_Y+BP_H-HDR_H; stub_bot = BP_Y+4*mm
    c.setFillColor(HexColor("#F0F6FF"))
    c.rect(stub_x+1*mm, stub_bot, STUB_W-2*mm, stub_top-stub_bot, fill=1, stroke=0)
    c.setFillColor(HexColor("#0077B6")); c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(stub_mid, stub_top-10*mm, "SEAT")
    c.setFillColor(HexColor("#0A2647")); c.setFont("Helvetica-Bold", 38)
    c.drawCentredString(stub_mid, stub_top-22*mm, td["seat"])
    c.setFont("Helvetica", 7); c.setFillColor(HexColor("#0077B6"))
    c.drawCentredString(stub_mid, stub_top-28*mm, "ECONOMY CLASS")
    c.setStrokeColor(HexColor("#BBCCDD")); c.setLineWidth(0.5)
    c.line(stub_x+4*mm, stub_top-32*mm, stub_x+STUB_W-4*mm, stub_top-32*mm)
    c.setFont("Helvetica", 7); c.setFillColor(HexColor("#888"))
    c.drawCentredString(stub_mid, stub_top-38*mm, "BOOKING REF / PNR")
    c.setFont("Helvetica-Bold", 15); c.setFillColor(HexColor("#0A2647"))
    c.drawCentredString(stub_mid, stub_top-46*mm, td["pnr"])
    c.setStrokeColor(HexColor("#BBCCDD"))
    c.line(stub_x+4*mm, stub_top-51*mm, stub_x+STUB_W-4*mm, stub_top-51*mm)
    c.setFont("Helvetica-Bold", 10); c.setFillColor(HexColor("#0A2647"))
    c.drawCentredString(stub_mid, stub_top-58*mm, f"{dep_code}  →  {arr_code}")
    c.setFont("Helvetica", 7); c.setFillColor(HexColor("#777"))
    c.drawCentredString(stub_mid, stub_top-64*mm, td.get("duration",""))
    c.setStrokeColor(HexColor("#BBCCDD"))
    c.line(stub_x+4*mm, stub_top-68*mm, stub_x+STUB_W-4*mm, stub_top-68*mm)
    qr_size = 30*mm; qr_x = stub_mid-qr_size/2; qr_y = stub_bot+14*mm
    _draw_qr_on_canvas(c, f"KVK-{td['pnr']}-{td['flight_number']}-{td['seat']}", qr_x, qr_y+qr_size, qr_size)
    c.setFont("Helvetica", 6); c.setFillColor(HexColor("#999"))
    c.drawCentredString(stub_mid, stub_bot+10*mm, "Scan at gate")
    c.setFont("Helvetica-Bold", 8); c.setFillColor(HexColor("#0077B6"))
    c.drawCentredString(stub_mid, stub_bot+4*mm, td["flight_number"])

def _draw_info_page(c, td, W, H):
    c.setFillColor(HexColor("#F8FAFF")); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#0A2647")); c.rect(0, H-28*mm, W, 28*mm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 18)
    c.drawString(18*mm, H-16*mm, "✈  KVK FLIGHTS FLYZZ — Booking Details & Important Information")
    c.setFont("Helvetica", 9); c.setFillColor(HexColor("#90CAF9"))
    c.drawRightString(W-18*mm, H-16*mm, f"PNR: {td['pnr']}  |  {td['pax_name']}  |  {td['flight_number']}")
    paid_y = H-44*mm
    c.setFillColor(HexColor("#E3F2FD")); c.roundRect(18*mm, paid_y, W-36*mm, 14*mm, 3*mm, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#0077B6")); c.setLineWidth(1.5)
    c.roundRect(18*mm, paid_y, W-36*mm, 14*mm, 3*mm, fill=0, stroke=1)
    c.setFillColor(HexColor("#0A2647")); c.setFont("Helvetica-Bold", 11)
    cur_code = td.get("currency_code","USD")
    c.drawString(24*mm, paid_y+5*mm,
                 f"You Have Paid: {fmt_currency(td['total_paid'],cur_code)}  ({cur_code})   |   "
                 f"Flight: {td['flight_number']}   |   "
                 f"Route: {td.get('dep_iata',td['departure'][:3]).upper()} ({td['departure']}) → "
                 f"{td.get('arr_iata',td['destination'][:3]).upper()} ({td['destination']})")
    tbl_y = paid_y-8*mm
    fields = [
        ("PNR / Booking Reference", td["pnr"]), ("Flight Number", td["flight_number"]),
        ("Airline", td["flight_name"]), ("Departure", f"{td['dep_time']}  (Terminal 1)"),
        ("Arrival", f"{td['arr_time']}  (Terminal 2)"), ("Duration", td.get("duration","—")),
        ("Type", "Non-Stop"), ("Seat", td["seat"]+"  (Economy Class)"),
        ("Checked Baggage", f"{td['luggage_kg']} kg"), ("Hand / Cabin Luggage", "7 kg"),
        ("Meal", td.get("meal_pref","Complimentary")), ("Ticket Purchase Date", td.get("booked_date","—")),
        ("Boarding Closes", td.get("boarding_closes","—")), ("Origin Country", td.get("dep_country","—")),
        ("Destination Country", td.get("arr_country","—")),
    ]
    col_w = (W-36*mm)/2
    for i, (k, v) in enumerate(fields):
        col, row = i%2, i//2
        cx = 18*mm+col*col_w; cy = tbl_y-row*11*mm
        c.setFillColor(HexColor("#F0F6FF") if i%4 < 2 else HexColor("#E8F0F8"))
        c.rect(cx, cy-7.5*mm, col_w-1*mm, 10*mm, fill=1, stroke=0)
        c.setFont("Helvetica", 7); c.setFillColor(HexColor("#888")); c.drawString(cx+2*mm, cy-1.5*mm, k.upper())
        c.setFont("Helvetica-Bold", 9); c.setFillColor(HexColor("#1A2A4A")); c.drawString(cx+2*mm, cy-7*mm, str(v))
    info_y = tbl_y-((len(fields)+1)//2)*11*mm-6*mm
    c.setStrokeColor(HexColor("#AABBCC")); c.setLineWidth(0.5)
    c.line(18*mm, info_y, W-18*mm, info_y); info_y -= 6*mm
    c.setFont("Helvetica-Bold", 11); c.setFillColor(HexColor("#0A2647"))
    c.drawString(18*mm, info_y, "IMPORTANT INFORMATION"); info_y -= 7*mm
    for line in IMPORTANT_INFO.strip().split("\n"):
        if info_y < 14*mm:
            c.showPage(); c.setFillColor(HexColor("#F8FAFF")); c.rect(0, 0, W, H, fill=1, stroke=0)
            info_y = H-18*mm
        stripped = line.strip()
        if not stripped: info_y -= 3*mm; continue
        if stripped.isupper() and not stripped.startswith("•") and len(stripped) < 60:
            info_y -= 2*mm; c.setFont("Helvetica-Bold", 9.5); c.setFillColor(HexColor("#0077B6"))
            c.drawString(18*mm, info_y, stripped); info_y -= 6*mm
        elif stripped.startswith("•"):
            c.setFont("Helvetica", 8.5); c.setFillColor(HexColor("#333"))
            txt = stripped
            while txt:
                if len(txt) <= 170: c.drawString(20*mm, info_y, txt); info_y -= 5*mm; break
                sp = txt[:170].rfind(" ")
                if sp < 0: sp = 170
                c.drawString(20*mm, info_y, txt[:sp]); info_y -= 5*mm
                txt = "  "+txt[sp:].lstrip()
        elif stripped.startswith("─"):
            c.setStrokeColor(HexColor("#AABBCC")); c.setLineWidth(0.5)
            c.line(18*mm, info_y+2*mm, W-18*mm, info_y+2*mm); info_y -= 5*mm
        else:
            c.setFont("Helvetica", 8.5); c.setFillColor(HexColor("#333"))
            c.drawString(18*mm, info_y, stripped); info_y -= 5*mm

# ══════════════════════════════════════════════════════════════
#  MAIN APPLICATION CLASS
# ══════════════════════════════════════════════════════════════
class KVKFlyzz(tk.Tk):
    WIZARD_STEPS = [
        "Passenger\nDetails", "Contact\nDetails",
        "Seat\nSelection",    "Meal &\nBaggage", "Payment",
    ]

    def __init__(self):
        super().__init__()
        self.title("✈  KVK FLIGHTS FLYZZ — Booking System")
        self.geometry("1280x800"); self.minsize(1100, 720)
        self.configure(bg=BG); self.resizable(True, True)
        _style_ttk(); self._center()
        self.user_id = None; self.user_name = None
        self._bk = {}; self._content = None
        self._img_cache = {}; self._selected_currency = "USD"
        self.show_login()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()-1280)//2; y = (self.winfo_screenheight()-800)//2
        self.geometry(f"1280x800+{x}+{y}")

    def _clear(self):
        for w in self.winfo_children(): w.destroy()

    # ─── reusable wizard header helpers ───────────────────────
    def _bk_flight_bar(self, parent):
        bk = self._bk
        dep_iata = bk.get("dep_iata","") or bk["departure"][:3].upper()
        arr_iata = bk.get("arr_iata","") or bk["destination"][:3].upper()
        bar = tk.Frame(parent, bg=ACCENT2); bar.pack(fill="x", padx=32, pady=(0,6), ipadx=12, ipady=6)
        tk.Label(bar,
                 text=(f"✈  {bk['flight_name']}  ({bk['flight_num']})   "
                       f"{dep_iata} → {arr_iata}   Dep: {bk['dep_time']}   Arr: {bk['arr_time']}   "
                       f"Duration: {bk.get('duration','—')}   Base fare: ${bk['cost']:.2f} USD"),
                 font=FS, bg=ACCENT2, fg=WHITE, anchor="w").pack(anchor="w", padx=8)

    def _wizard_section(self, parent, title):
        f = tk.Frame(parent, bg=BG); f.pack(fill="x", padx=32, pady=(14,2))
        lbl(f, title, FH3, ACCENT, BG).pack(anchor="w")
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=32, pady=2)

    # ════════════════════════════════════════════════════════
    #  LOGIN
    # ════════════════════════════════════════════════════════
    def show_login(self):
        self._clear(); self.user_id = None
        outer = tk.Frame(self, bg=BG); outer.pack(fill="both", expand=True)
        left = tk.Frame(outer, bg=PANEL, width=420); left.pack(side="left", fill="y")
        left.pack_propagate(False)
        brand = tk.Frame(left, bg=PANEL); brand.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(brand, text="✈", font=("Segoe UI",64), bg=PANEL, fg=ACCENT).pack()
        tk.Label(brand, text="KVK FLIGHTS", font=("Segoe UI",28,"bold"), bg=PANEL, fg=WHITE).pack(pady=(8,0))
        tk.Label(brand, text="FLYZZ", font=("Segoe UI",22,"bold"), bg=PANEL, fg=ACCENT).pack()
        tk.Label(brand, text="Your Wings. Your Journey.", font=("Segoe UI",11), bg=PANEL, fg=GREY).pack(pady=(12,0))
        tk.Frame(brand, bg=ACCENT, height=2, width=120).pack(pady=16)
        for txt in ["✓  5-Step Guided Booking Wizard",
                    "✓  IATA Airport Autocomplete Search",
                    "✓  Real Airline Seat Map (3-3 Layout)",
                    "✓  E-Ticket Download in My Bookings"]:
            tk.Label(brand, text=txt, font=FS, bg=PANEL, fg=GREY).pack(anchor="w")
        right = tk.Frame(outer, bg=BG); right.pack(side="right", fill="both", expand=True)
        form = tk.Frame(right, bg=BG); form.place(relx=0.5, rely=0.5, anchor="center")
        lbl(form, "Welcome Back", ("Segoe UI",26,"bold"), WHITE, BG, "center").pack(pady=(0,4))
        lbl(form, "Sign in to continue", FB, GREY, BG, "center").pack(pady=(0,24))
        c = card_f(form); c.pack(ipadx=30, ipady=24)
        lbl(c, "Username", FL, GREY, CARD).pack(anchor="w", padx=16, pady=(14,2))
        self._lu = entry_w(c, width=30); self._lu.pack(padx=16, pady=(0,8))
        lbl(c, "Password", FL, GREY, CARD).pack(anchor="w", padx=16, pady=(0,2))
        self._lp = entry_w(c, width=30, show="●"); self._lp.pack(padx=16, pady=(0,10))
        rf = tk.Frame(c, bg=CARD); rf.pack(padx=16, pady=6)
        self._role = tk.StringVar(value="user")
        for val, txt in [("user"," Passenger "),("admin"," Admin ")]:
            tk.Radiobutton(rf, text=txt, variable=self._role, value=val,
                           bg=CARD, fg=GREY, selectcolor=INPUT_BG,
                           activebackground=CARD, activeforeground=ACCENT,
                           font=FB, indicatoron=0, relief="flat",
                           padx=14, pady=5, cursor="hand2").pack(side="left", padx=4)
        btn_w(c, "Sign In  →", self._do_login, w=30, font=FH3).pack(padx=16, pady=14)
        tk.Button(c, text="New passenger? Register →", command=self.show_register,
                  bg=CARD, fg=ACCENT, font=FS, relief="flat", cursor="hand2",
                  activebackground=CARD).pack(pady=(0,10))
        self._lu.bind("<Return>", lambda e: self._lp.focus())
        self._lp.bind("<Return>", lambda e: self._do_login())
        self._lu.focus()

    def _do_login(self):
        u = self._lu.get().strip(); p = self._lp.get().strip()
        if not u or not p: messagebox.showwarning("Missing","Enter username and password."); return
        try:
            conn = _conn(); cur = conn.cursor()
            if self._role.get() == "admin":
                cur.execute("SELECT id FROM admins WHERE username=%s AND password_hash=%s", (u, _sha(p)))
                row = cur.fetchone(); cur.close(); conn.close()
                if row: self.show_admin()
                else: messagebox.showerror("Failed","Invalid admin credentials.")
            else:
                cur.execute("SELECT id,first_name,last_name FROM users "
                            "WHERE username=%s AND password_hash=%s AND is_deleted=0", (u, _sha(p)))
                row = cur.fetchone(); cur.close(); conn.close()
                if row:
                    self.user_id = row[0]; self.user_name = f"{row[1]} {row[2]}"; self.show_user_home()
                else: messagebox.showerror("Failed","Invalid credentials.")
        except Error as e: messagebox.showerror("DB Error", str(e))

    # ════════════════════════════════════════════════════════
    #  REGISTER
    # ════════════════════════════════════════════════════════
    def show_register(self):
        self._clear()
        outer = tk.Frame(self, bg=BG); outer.pack(fill="both", expand=True)
        top = tk.Frame(outer, bg=BG); top.pack(fill="x", padx=30, pady=14)
        tk.Button(top, text="← Back to Login", command=self.show_login,
                  bg=BG, fg=ACCENT, font=FL, relief="flat", cursor="hand2").pack(side="left")
        lbl(top, "✈ KVK FLYZZ", FH3, WHITE, BG, "e").pack(side="right")
        lbl(outer, "Create Your Account", FT, WHITE, BG, "center").pack(pady=(0,4))
        lbl(outer, "Fill in the details below to get started", FB, GREY, BG, "center").pack(pady=(0,18))
        c = card_f(outer); c.pack(padx=160, ipadx=30, ipady=24)
        grid = tk.Frame(c, bg=CARD); grid.pack(padx=10, pady=8)
        self._re = {}
        for fn1, k1, fn2, k2, s2 in [
            ("First Name *","first_name","Last Name *","last_name",None),
            ("Username *","username","Password *","password","●"),
        ]:
            row = tk.Frame(grid, bg=CARD); row.pack(pady=6)
            for fn, key, show in [(fn1,k1,None),(fn2,k2,s2)]:
                col = tk.Frame(row, bg=CARD); col.pack(side="left", padx=14)
                lbl(col, fn, FL, GREY, CARD).pack(anchor="w")
                e = entry_w(col, width=22, show=show); e.pack()
                self._re[key] = e
        rp_f = tk.Frame(c, bg=CARD); rp_f.pack(pady=(0,8))
        lbl(rp_f, "Re-enter Password *", FL, GREY, CARD).pack(anchor="w", padx=16)
        self._rp2 = entry_w(rp_f, width=22, show="●"); self._rp2.pack(padx=16)
        btn_w(c, "Create Account  ✓", self._do_register, bg=SUCCESS, fg=DARK_TEXT, w=30, font=FH3).pack(pady=16)

    def _do_register(self):
        v = {k: e.get().strip() for k, e in self._re.items()}
        rp = self._rp2.get().strip()
        if any(not x for x in v.values()) or not rp:
            messagebox.showwarning("Missing","All fields required."); return
        if v["password"] != rp: messagebox.showerror("Mismatch","Passwords do not match."); return
        if len(v["password"]) < 6: messagebox.showerror("Weak","Min 6 characters."); return
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("INSERT INTO users(first_name,last_name,username,password_hash) VALUES(%s,%s,%s,%s)",
                        (v["first_name"],v["last_name"],v["username"],_sha(v["password"])))
            conn.commit(); cur.close(); conn.close()
            messagebox.showinfo("Success","Account created! You can now log in."); self.show_login()
        except Error as e:
            if "Duplicate" in str(e): messagebox.showerror("Taken","Username already exists.")
            else: messagebox.showerror("DB", str(e))

    # ════════════════════════════════════════════════════════
    #  ADMIN
    # ════════════════════════════════════════════════════════
    def show_admin(self):
        nav = [
            ("📊   Overview",         self._admin_overview),
            ("✈    Add Flight",        self._admin_add_flight),
            ("📋   Manage Flights",    self._admin_manage_flights),
            ("👥   Passenger Records", self._admin_passengers),
            ("🔐   User Accounts",     self._admin_user_accounts),
            ("📥   Reports",           self._admin_reports),
        ]
        _, self._content = build_sidebar_layout(self, nav, self.show_login, "Admin Panel")
        self._admin_overview()

    def _admin_overview(self):
        clear_content(self._content)
        page_header(self._content, "Dashboard", f"Admin Panel  •  {datetime.now():%d %b %Y  %I:%M %p}")
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM flights WHERE status='active' AND is_deleted=0"); af = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE is_deleted=0"); tu = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM bookings WHERE is_deleted=0"); tb = cur.fetchone()[0]
            cur.execute("SELECT IFNULL(SUM(total_paid),0) FROM bookings WHERE is_deleted=0"); rev = float(cur.fetchone()[0])
            cur.close(); conn.close()
        except: af = tu = tb = 0; rev = 0.0
        stat_row = tk.Frame(self._content, bg=BG); stat_row.pack(fill="x", padx=32, pady=8)
        for title, val, col in [("Active Flights",af,ACCENT),("Registered Users",tu,SUCCESS),
                                  ("Total Bookings",tb,WARNING),("Revenue (USD)",f"${rev:,.2f}","#FF6D3B")]:
            c = card_f(stat_row); c.pack(side="left", padx=(0,14), ipadx=18, ipady=14)
            lbl(c, str(val), ("Segoe UI",24,"bold"), col, CARD, "center").pack(pady=(14,2))
            lbl(c, title, FS, GREY, CARD, "center").pack(pady=(0,12))
        lbl(self._content, "Recent Bookings", FH3, WHITE, BG).pack(anchor="w", padx=32, pady=(18,4))
        self._render_bookings_tree(self._content, limit=8)

    def _admin_add_flight(self):
        clear_content(self._content)
        page_header(self._content, "Add New Flight")
        scroll = tk.Frame(self._content, bg=BG); scroll.pack(fill="both", expand=True, padx=32)
        c = card_f(scroll); c.pack(fill="x", ipadx=28, ipady=20, pady=4)
        self._af = {}

        def row2(l1, k1, l2, k2):
            rf = tk.Frame(c, bg=CARD); rf.pack(fill="x", padx=16, pady=4)
            for ln, key in [(l1,k1),(l2,k2)]:
                col = tk.Frame(rf, bg=CARD); col.pack(side="left", padx=8, fill="x", expand=True)
                lbl(col, ln, FL, GREY, CARD).pack(anchor="w")
                e = entry_w(col, width=26); e.pack(fill="x"); self._af[key] = e

        row2("Flight Name *","flight_name","Flight Number *","flight_number")
        iata_row = tk.Frame(c, bg=CARD); iata_row.pack(fill="x", padx=16, pady=4)
        for side_lbl_t, key_iata, key_city in [
            ("Departure IATA *","dep_iata","departure_area"),
            ("Destination IATA *","arr_iata","destination_area"),
        ]:
            col = tk.Frame(iata_row, bg=CARD); col.pack(side="left", padx=8, fill="x", expand=True)
            lbl(col, side_lbl_t+" (type code or city)", FL, GREY, CARD).pack(anchor="w")
            city_e = entry_w(col, width=28)
            iata_widget = IATAEntry(col, bg=CARD, width=10,
                                    on_select=lambda code,name,city,country,ce=city_e:
                                        (ce.delete(0,"end"), ce.insert(0, f"{city}, {country}")))
            iata_widget.pack(anchor="w"); city_e.pack(anchor="w", pady=(4,0))
            lbl(col, "Full area name (auto-filled on selection)", FS, GREY, CARD).pack(anchor="w")
            self._af[key_iata] = iata_widget; self._af[key_city] = city_e

        def make_dt_picker(label_text, key_prefix):
            rf = tk.Frame(c, bg=CARD); rf.pack(fill="x", padx=16, pady=4)
            lbl(rf, label_text, FL, GREY, CARD).pack(anchor="w", pady=(0,3))
            row_f = tk.Frame(rf, bg=CARD); row_f.pack(anchor="w")
            _date_var = tk.StringVar(); _hour_var = tk.StringVar(value="00"); _min_var = tk.StringVar(value="00")
            tk.Label(row_f, textvariable=_date_var, bg=INPUT_BG, fg=WHITE, font=FB, width=14,
                     anchor="w", padx=6, highlightthickness=1, highlightbackground=BORDER
                     ).pack(side="left", ipady=5)
            tk.Button(row_f, text="📅", command=lambda: open_calendar(_date_var),
                      bg=ACCENT2, fg=WHITE, font=FB, relief="flat", cursor="hand2",
                      padx=8, pady=4).pack(side="left", padx=(6,10))
            tk.Label(row_f, text="Time:", font=FL, bg=CARD, fg=GREY).pack(side="left", padx=(0,4))
            for var, to in [(_hour_var,23),(_min_var,59)]:
                tk.Spinbox(row_f, from_=0, to=to, width=3, textvariable=var, format="%02.0f",
                           bg=INPUT_BG, fg=WHITE, font=FB, buttonbackground=BORDER,
                           relief="flat", insertbackground=ACCENT, wrap=True).pack(side="left")
                if var is _hour_var:
                    tk.Label(row_f, text=":", font=FH3, bg=CARD, fg=GREY).pack(side="left", padx=2)

            class _Proxy:
                def get(self_inner):
                    d = _date_var.get().strip()
                    return f"{d} {_hour_var.get().zfill(2)}:{_min_var.get().zfill(2)}" if d else ""
            self._af[key_prefix] = _Proxy()

        make_dt_picker("Departure Date & Time *", "dep_time")
        make_dt_picker("Arrival Date & Time *",   "arr_time")
        row2("Ticket Cost (USD) *","ticket_cost","Total Seats *","total_seats")
        row2("Luggage Allowance (kg)","luggage_kg","Initial Seats Booked","seats_booked")

        self._img_path_var = tk.StringVar(value="")
        img_sec = tk.Frame(c, bg=CARD); img_sec.pack(fill="x", padx=16, pady=8)
        lbl(img_sec, "🖼  Airline Image (optional)", FH3, ACCENT, CARD).pack(anchor="w")
        img_row = tk.Frame(img_sec, bg=CARD); img_row.pack(fill="x", pady=4)
        tk.Entry(img_row, textvariable=self._img_path_var, bg=INPUT_BG, fg=GREY, relief="flat",
                 font=FS, width=52, state="readonly", highlightthickness=1,
                 highlightbackground=BORDER).pack(side="left", padx=(0,8))
        btn_w(img_row, "📂 Browse",
              lambda: self._img_path_var.set(
                  filedialog.askopenfilename(
                      filetypes=[("Images","*.png *.jpg *.jpeg *.gif *.bmp *.webp")]) or self._img_path_var.get()),
              bg=ACCENT2, w=14, font=FL).pack(side="left")
        tk.Frame(c, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(6,4))
        btn_w(c, "Add Flight  ✓", self._do_add_flight, bg=SUCCESS, fg=DARK_TEXT, w=24, font=FH3).pack(pady=14)

    def _do_add_flight(self):
        v = {k: (e.get().strip() if hasattr(e,'get') and callable(e.get) else "") for k, e in self._af.items()}
        required = ["flight_name","flight_number","departure_area","destination_area",
                    "dep_time","arr_time","ticket_cost","total_seats"]
        if any(not v.get(k,"") for k in required):
            messagebox.showwarning("Missing","Fill all required fields."); return
        try:
            dep = datetime.strptime(v["dep_time"], "%Y-%m-%d %H:%M")
            arr = datetime.strptime(v["arr_time"], "%Y-%m-%d %H:%M")
            if arr <= dep: raise ValueError("Arrival must be after departure")
            cost = float(v["ticket_cost"]); seats = int(v["total_seats"])
            lug = int(v["luggage_kg"]) if v.get("luggage_kg") else 30
            bkd = int(v["seats_booked"]) if v.get("seats_booked") else 0
        except ValueError as e: messagebox.showerror("Format", str(e)); return
        img = self._img_path_var.get().strip() or None
        dep_iata = v.get("dep_iata","").upper(); arr_iata = v.get("arr_iata","").upper()
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute(
                """INSERT INTO flights
                   (flight_name,flight_number,departure_area,destination_area,
                    departure_iata,destination_iata,departure_time,arrival_time,
                    ticket_cost,total_seats,seats_booked,luggage_kg,image_path)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (v["flight_name"],v["flight_number"],v["departure_area"],v["destination_area"],
                 dep_iata,arr_iata,dep,arr,cost,seats,bkd,lug,img))
            conn.commit(); cur.close(); conn.close()
            messagebox.showinfo("Added",f"Flight {v['flight_number']} added!"); self._admin_add_flight()
        except Error as e:
            if "Duplicate" in str(e): messagebox.showerror("Duplicate","Flight number exists.")
            else: messagebox.showerror("DB", str(e))

    def _admin_manage_flights(self):
        clear_content(self._content)
        page_header(self._content, "Manage Flights", "Soft-archive only.")
        top = tk.Frame(self._content, bg=BG); top.pack(fill="x", padx=32, pady=(0,8))
        btn_w(top, "↻ Refresh", self._load_admin_flights, w=12).pack(side="right")
        btn_w(top, "🗄 Archive", self._remove_flight, bg=WARNING, fg=DARK_TEXT, w=16).pack(side="right", padx=(0,8))
        btn_w(top, "✈ Cancel Flight", self._cancel_flight_status, bg=DANGER, w=18).pack(side="right", padx=(0,8))
        cols = ("S.No","Flight Name","Number","From","To","IATA Route",
                "Departure","Arrival","Duration","Cost","Seats","Booked","Status")
        widths = [45,130,85,120,120,100,140,140,80,70,60,60,80]
        self._fl_tree, _ = make_tree(self._content, cols, widths)
        self._content.children[list(self._content.children)[-1]].pack(fill="both", expand=True, padx=32, pady=4)
        self._load_admin_flights()

    def _load_admin_flights(self):
        self._fl_tree.delete(*self._fl_tree.get_children())
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute(
                """SELECT id,flight_name,flight_number,departure_area,destination_area,
                          CONCAT(IFNULL(departure_iata,'?'),' → ',IFNULL(destination_iata,'?')),
                          DATE_FORMAT(departure_time,'%d %b %Y %H:%i'),
                          DATE_FORMAT(arrival_time,'%d %b %Y %H:%i'),
                          departure_time,arrival_time,ticket_cost,total_seats,seats_booked,status
                   FROM flights WHERE is_deleted=0 ORDER BY departure_time""")
            for sno, r in enumerate(cur.fetchall(), 1):
                fid = r[0]; dep_dt = r[8]; arr_dt = r[9]
                dur = _duration_str(dep_dt, arr_dt) if dep_dt and arr_dt else "—"
                tag = "cancelled" if r[13] == "cancelled" else ""
                self._fl_tree.insert("","end",
                    values=(sno,r[1],r[2],r[3],r[4],r[5],r[6],r[7],dur,r[10],r[11],r[12],r[13]),
                    tags=(tag,), iid=str(fid))
            self._fl_tree.tag_configure("cancelled", foreground=DANGER)
            cur.close(); conn.close()
        except Error as e: messagebox.showerror("DB", str(e))

    def _remove_flight(self):
        sel = self._fl_tree.selection()
        if not sel: messagebox.showwarning("Select","Choose a flight."); return
        fid = int(sel[0]); fn = self._fl_tree.item(sel[0])["values"][2]
        if not messagebox.askyesno("Confirm", f"Archive flight {fn}?"): return
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("UPDATE flights SET is_deleted=1 WHERE id=%s", (fid,))
            conn.commit(); cur.close(); conn.close(); self._load_admin_flights()
        except Error as e: messagebox.showerror("DB", str(e))

    def _cancel_flight_status(self):
        sel = self._fl_tree.selection()
        if not sel: messagebox.showwarning("Select","Choose a flight."); return
        fid = int(sel[0]); fn = self._fl_tree.item(sel[0])["values"][2]
        if not messagebox.askyesno("Confirm", f"Mark {fn} as CANCELLED?"): return
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("UPDATE flights SET status='cancelled' WHERE id=%s", (fid,))
            conn.commit(); cur.close(); conn.close(); self._load_admin_flights()
        except Error as e: messagebox.showerror("DB", str(e))

    def _admin_passengers(self):
        clear_content(self._content)
        page_header(self._content, "Passenger Records", "All active bookings")
        cols = ("S.No","PNR","Passenger","Flight","Route","Seat",
                "Passport","Country","Email","Mobile","Currency","Fare","Booked On")
        widths = [50,70,140,90,160,55,100,100,160,100,60,80,130]
        tree, tf = make_tree(self._content, cols, widths, height=16)
        tf.pack(fill="both", expand=True, padx=32, pady=4)
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute(
                """SELECT b.pnr, CONCAT(b.pax_first_name,' ',b.pax_last_name),
                          f.flight_number,
                          CONCAT(f.departure_area,' → ',f.destination_area),
                          b.seat, b.passport_no, b.issue_country,
                          b.email, b.mobile,
                          IFNULL(b.currency_code,'USD'), b.total_paid,
                          DATE_FORMAT(b.booking_date,'%d %b %Y %H:%i')
                   FROM bookings b JOIN flights f ON b.flight_id=f.id
                   WHERE b.is_deleted=0 ORDER BY b.booking_date DESC""")
            for sno, r in enumerate(cur.fetchall(), 1): tree.insert("","end", values=(sno,)+r)
            cur.close(); conn.close()
        except Error as e: messagebox.showerror("DB", str(e))

    def _admin_user_accounts(self):
        clear_content(self._content)
        page_header(self._content, "User Accounts")
        sf = tk.Frame(self._content, bg=BG); sf.pack(fill="x", padx=32, pady=(0,6))
        lbl(sf, "Search:", FL, GREY, BG).pack(side="left")
        self._ua_search = entry_w(sf, width=28); self._ua_search.pack(side="left", padx=8)
        btn_w(sf, "🔍 Search", self._ua_do_search, w=12).pack(side="left", padx=(0,8))
        btn_w(sf, "↻ Show All", self._ua_load_all, w=12).pack(side="left")
        self._ua_search.bind("<Return>", lambda e: self._ua_do_search())
        cols = ("S.No","First Name","Last Name","Username","Joined"); widths = [55,160,160,160,160]
        self._ua_tree, tf = make_tree(self._content, cols, widths, height=8)
        tf.pack(fill="both", expand=True, padx=32, pady=4)
        self._ua_tree.bind("<ButtonRelease-1>", self._ua_on_select)
        det = card_f(self._content); det.pack(fill="x", padx=32, pady=(4,8), ipadx=20, ipady=14)
        lbl(det, "🔐  Identity Verification", FH3, ACCENT, CARD).pack(anchor="w", padx=16, pady=(10,6))
        tk.Frame(det, bg=BORDER, height=1).pack(fill="x", padx=16, pady=2)
        self._ua_detail_rows = {}
        grid_f = tk.Frame(det, bg=CARD); grid_f.pack(fill="x", padx=16, pady=8)
        for i, (label_t, key) in enumerate([("Full Name","name"),("Username","uname"),
                                             ("Account Since","since"),("Total Bookings","bookings")]):
            col_f = tk.Frame(grid_f, bg=CARD); col_f.grid(row=i//2, column=i%2, padx=20, pady=4, sticky="w")
            lbl(col_f, label_t, FS, GREY, CARD).pack(anchor="w")
            val_lbl = lbl(col_f, "—", FL, WHITE, CARD); val_lbl.pack(anchor="w")
            self._ua_detail_rows[key] = val_lbl
        verify_f = tk.Frame(det, bg=CARD); verify_f.pack(fill="x", padx=16, pady=6)
        lbl(verify_f, "🔑  Verify Password:", FL, GREY, CARD).pack(anchor="w")
        vrow = tk.Frame(verify_f, bg=CARD); vrow.pack(anchor="w", pady=4)
        self._ua_pw_entry = entry_w(vrow, width=28, show="●"); self._ua_pw_entry.pack(side="left", padx=(0,8))
        btn_w(vrow, "✓ Verify", self._ua_verify_password, w=14, bg=SUCCESS, fg=DARK_TEXT).pack(side="left")
        self._ua_verify_result = lbl(vrow, "", FB, WHITE, CARD); self._ua_verify_result.pack(side="left", padx=12)
        self._ua_selected_hash = None; self._ua_selected_uid = None
        self._ua_load_all()

    def _ua_load_all(self):
        self._ua_tree.delete(*self._ua_tree.get_children()); self._ua_clear_detail()
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("SELECT id,first_name,last_name,username,"
                        "DATE_FORMAT(created_at,'%d %b %Y') "
                        "FROM users WHERE is_deleted=0 ORDER BY created_at DESC")
            for sno, r in enumerate(cur.fetchall(), 1):
                self._ua_tree.insert("","end", values=(sno,r[1],r[2],r[3],r[4]), iid=str(r[0]))
            cur.close(); conn.close()
        except Error as e: messagebox.showerror("DB", str(e))

    def _ua_do_search(self):
        q = self._ua_search.get().strip()
        if not q: self._ua_load_all(); return
        self._ua_tree.delete(*self._ua_tree.get_children()); self._ua_clear_detail()
        try:
            conn = _conn(); cur = conn.cursor(); like = f"%{q}%"
            cur.execute("SELECT id,first_name,last_name,username,"
                        "DATE_FORMAT(created_at,'%d %b %Y') "
                        "FROM users WHERE is_deleted=0 "
                        "AND (username LIKE %s OR first_name LIKE %s OR last_name LIKE %s) "
                        "ORDER BY created_at DESC", (like,like,like))
            for sno, r in enumerate(cur.fetchall(), 1):
                self._ua_tree.insert("","end", values=(sno,r[1],r[2],r[3],r[4]), iid=str(r[0]))
            cur.close(); conn.close()
        except Error as e: messagebox.showerror("DB", str(e))

    def _ua_on_select(self, event=None):
        sel = self._ua_tree.selection()
        if not sel: return
        uid = int(sel[0])
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("SELECT id,first_name,last_name,username,password_hash,"
                        "DATE_FORMAT(created_at,'%d %b %Y %H:%i') FROM users WHERE id=%s", (uid,))
            row = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM bookings WHERE user_id=%s AND is_deleted=0", (uid,))
            bk_count = cur.fetchone()[0]; cur.close(); conn.close()
        except Error as e: messagebox.showerror("DB", str(e)); return
        if not row: return
        uid_v, fn, ln, uname, phash, since = row
        self._ua_selected_hash = phash; self._ua_selected_uid = uid_v
        self._ua_pw_entry.delete(0,"end"); self._ua_verify_result.config(text="", fg=WHITE)
        self._ua_detail_rows["name"].config(text=f"{fn} {ln}")
        self._ua_detail_rows["uname"].config(text=uname)
        self._ua_detail_rows["since"].config(text=since)
        self._ua_detail_rows["bookings"].config(text=f"{bk_count} booking(s)")

    def _ua_clear_detail(self):
        self._ua_selected_hash = None
        for _, lbl_w in self._ua_detail_rows.items(): lbl_w.config(text="—")
        if hasattr(self,"_ua_verify_result"): self._ua_verify_result.config(text="", fg=WHITE)

    def _ua_verify_password(self):
        if not self._ua_selected_hash: messagebox.showwarning("No User","Select a user."); return
        pw = self._ua_pw_entry.get()
        if not pw: messagebox.showwarning("Empty","Enter a password."); return
        if _sha(pw) == self._ua_selected_hash:
            self._ua_verify_result.config(text="✓  Password matches!", fg=SUCCESS)
        else:
            self._ua_verify_result.config(text="✗  Does NOT match.", fg=DANGER)

    def _admin_reports(self):
        clear_content(self._content)
        page_header(self._content, "Flight Reports")
        c = card_f(self._content); c.pack(padx=32, fill="x", ipadx=20, ipady=12)
        lbl(c, "Flight Summary Report", FH3, WHITE, CARD).pack(anchor="w", padx=16, pady=(12,4))
        bf = tk.Frame(c, bg=CARD); bf.pack(anchor="w", padx=16, pady=8)
        btn_w(bf, "Preview", self._preview_report, w=14).pack(side="left", padx=(0,8))
        btn_w(bf, "Download CSV  ↓", self._download_csv, bg=SUCCESS, fg=DARK_TEXT, w=18).pack(side="left")
        self._rep_txt = tk.Text(self._content, bg=CARD, fg=WHITE, font=FM, relief="flat",
                                state="disabled", highlightthickness=1, highlightbackground=BORDER)
        self._rep_txt.pack(fill="both", expand=True, padx=32, pady=(12,20))

    def _report_rows(self):
        conn = _conn(); cur = conn.cursor()
        cur.execute(
            """SELECT f.flight_number, f.flight_name, f.departure_area,
                      f.destination_area,
                      DATE_FORMAT(f.departure_time,'%d %b %Y %H:%i'),
                      f.total_seats, COUNT(b.id),
                      (f.total_seats - COUNT(b.id)),
                      IFNULL(SUM(b.total_paid), 0)
               FROM flights f
               LEFT JOIN bookings b ON b.flight_id=f.id AND b.is_deleted=0
               WHERE f.is_deleted=0
               GROUP BY f.id ORDER BY f.departure_time""")
        rows = cur.fetchall(); cur.close(); conn.close(); return rows

    def _preview_report(self):
        rows = self._report_rows()
        lines = ["="*95,"  KVK FLIGHTS FLYZZ — FLIGHT SUMMARY REPORT",
                 f"  Generated: {datetime.now():%d %b %Y  %I:%M %p}","="*95,
                 f"{'Flt#':<10}{'Name':<22}{'From':<16}{'To':<16}{'Departure':<20}{'Tot':<6}{'Bkd':<6}{'Avl':<6}{'Revenue':>14}",
                 "-"*95]
        for r in rows:
            lines.append(f"{r[0]:<10}{str(r[1]):<22}{str(r[2]):<16}{str(r[3]):<16}"
                         f"{str(r[4]):<20}{r[5]:<6}{r[6]:<6}{r[7]:<6}${float(r[8]):>13,.2f}")
        lines.append("="*95)
        self._rep_txt.config(state="normal"); self._rep_txt.delete(1.0,"end")
        self._rep_txt.insert("end", "\n".join(lines)); self._rep_txt.config(state="disabled")

    def _download_csv(self):
        import csv; rows = self._report_rows()
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV","*.csv")],
                                            initialfile=f"KVKFlyzz_{datetime.now():%Y%m%d}.csv")
        if not path: return
        with open(path,"w",newline="",encoding="utf-8") as fp:
            w = csv.writer(fp)
            w.writerow(["Flight#","Name","From","To","Departure","Total Seats","Booked","Available","Revenue (USD)"])
            w.writerows(rows)
        messagebox.showinfo("Saved", f"Saved:\n{path}")

    # ════════════════════════════════════════════════════════
    #  USER HOME
    # ════════════════════════════════════════════════════════
    def show_user_home(self):
        nav = [("✈    Browse & Search Flights", self._user_flights),
               ("📋   My Bookings",              self._user_bookings)]
        _, self._content = build_sidebar_layout(self, nav, self.show_login, self.user_name or "")
        self._user_flights()

    # ════════════════════════════════════════════════════════
    #  USER — BROWSE FLIGHTS
    # ════════════════════════════════════════════════════════
    def _user_flights(self, search_params=None):
        clear_content(self._content)
        page_header(self._content, "Browse & Search Flights",
                    "Type IATA code or city name — autocomplete will suggest airports")
        fc = card_f(self._content); fc.pack(fill="x", padx=32, pady=(0,10), ipadx=16, ipady=12)
        lbl(fc, "🔍  Flight Search", FH3, ACCENT, CARD).pack(anchor="w", padx=16, pady=(10,6))
        f1 = tk.Frame(fc, bg=CARD); f1.pack(fill="x", padx=16, pady=2)

        def search_col(f1, label_text):
            c = tk.Frame(f1, bg=CARD); c.pack(side="left", padx=(0,12))
            lbl(c, label_text, FL, GREY, CARD).pack(anchor="w")
            return c

        c1 = search_col(f1, "From (IATA or City)")
        self._s_dep_widget = IATAEntry(c1, bg=CARD, width=8); self._s_dep_widget.pack(anchor="w", pady=(2,0))
        c2 = search_col(f1, "To (IATA or City)")
        self._s_dst_widget = IATAEntry(c2, bg=CARD, width=8); self._s_dst_widget.pack(anchor="w", pady=(2,0))

        c3 = tk.Frame(f1, bg=CARD); c3.pack(side="left", padx=(0,12))
        date_f, self._s_date_proxy = make_calendar_picker(c3, "Travel Date", bg=CARD); date_f.pack()

        c4 = search_col(f1, "Passengers")
        self._s_pax = tk.Spinbox(c4, from_=1, to=10, width=5, bg=INPUT_BG, fg=WHITE, font=FB,
                                  buttonbackground=BORDER, relief="flat", insertbackground=ACCENT, wrap=False)
        self._s_pax.pack(ipady=5)

        c5 = tk.Frame(f1, bg=CARD); c5.pack(side="left", padx=(4,0))
        lbl(c5, " ", FS, GREY, CARD).pack()
        bf = tk.Frame(c5, bg=CARD); bf.pack()
        btn_w(bf, "🔍 Search", self._do_search_flights, w=12, bg=SUCCESS, fg=DARK_TEXT).pack(side="left", padx=(0,4))
        btn_w(bf, "✕ Clear", self._clear_search, w=8, bg=DANGER).pack(side="left")
        lbl(fc, "ℹ  Type a 3-letter code (MAA, DXB) or city name — a dropdown will appear.", FS, GREY, CARD
            ).pack(anchor="w", padx=16, pady=(4,6))

        if search_params:
            if search_params.get("dep"): self._s_dep_widget.set(search_params["dep"])
            if search_params.get("dst"): self._s_dst_widget.set(search_params["dst"])
            if search_params.get("date"): self._s_date_proxy.set(search_params["date"])
            if search_params.get("pax"):
                self._s_pax.delete(0,"end"); self._s_pax.insert(0, search_params["pax"])

        flights = self._fetch_flights(search_params)
        lbl(self._content, f"  {len(flights)} flight(s) found",
            FB, ACCENT if flights else DANGER, BG).pack(anchor="w", padx=32, pady=(0,4))

        outer = tk.Frame(self._content, bg=BG); outer.pack(fill="both", expand=True, padx=32, pady=4)
        canvas_c = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas_c.yview, style="KVK.Vertical.TScrollbar")
        canvas_c.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); canvas_c.pack(side="left", fill="both", expand=True)
        cards_frame = tk.Frame(canvas_c, bg=BG)
        win_id = canvas_c.create_window((0,0), window=cards_frame, anchor="nw")
        canvas_c.bind("<Configure>", lambda e: canvas_c.itemconfig(win_id, width=e.width))
        cards_frame.bind("<Configure>", lambda e: canvas_c.configure(scrollregion=canvas_c.bbox("all")))
        canvas_c.bind_all("<MouseWheel>", lambda e: canvas_c.yview_scroll(int(-1*(e.delta/120)),"units"))

        self._img_cache = {}
        if not flights:
            lbl(cards_frame, "No flights found. Try different IATA codes or clear the search.", FB, GREY, BG).pack(pady=40)
        else:
            for row in flights:
                (fid,fname,fnum,dep,dst,dep_iata,dst_iata,
                 dep_t,arr_t,dep_dt,arr_dt,cost,total_seats,seats_booked,img_path) = row
                avail = int(total_seats)-int(seats_booked)
                dur = _duration_str(dep_dt,arr_dt) if dep_dt and arr_dt else "—"
                self._build_flight_card(cards_frame, canvas_c, fid, fname, fnum,
                                        dep, dst, dep_iata or "", dst_iata or "",
                                        dep_t, arr_t, dur, float(cost),
                                        int(total_seats), avail, img_path)

    def _fetch_flights(self, params=None):
        try:
            conn = _conn(); cur = conn.cursor()
            query = (
                "SELECT f.id,f.flight_name,f.flight_number,"
                "f.departure_area,f.destination_area,"
                "f.departure_iata,f.destination_iata,"
                "DATE_FORMAT(f.departure_time,'%d %b %Y %H:%i'),"
                "DATE_FORMAT(f.arrival_time,'%d %b %Y %H:%i'),"
                "f.departure_time,f.arrival_time,"
                "f.ticket_cost,f.total_seats,f.seats_booked,f.image_path "
                "FROM flights f "
                "WHERE f.status='active' AND f.is_deleted=0 "
                "AND f.departure_time > NOW() "
                "AND (f.total_seats - f.seats_booked) > 0")
            args = []
            if params:
                dep = params.get("dep","").strip().upper()
                dst = params.get("dst","").strip().upper()
                date_val = params.get("date","").strip()
                pax = params.get("pax",1)
                if dep:
                    query += " AND (UPPER(f.departure_iata) LIKE %s OR LOWER(f.departure_area) LIKE LOWER(%s))"
                    args += [f"%{dep}%", f"%{dep}%"]
                if dst:
                    query += " AND (UPPER(f.destination_iata) LIKE %s OR LOWER(f.destination_area) LIKE LOWER(%s))"
                    args += [f"%{dst}%", f"%{dst}%"]
                if date_val: query += " AND DATE(f.departure_time) = %s"; args.append(date_val)
                if pax and int(pax) > 1:
                    query += " AND (f.total_seats - f.seats_booked) >= %s"; args.append(int(pax))
            query += " ORDER BY f.departure_time"
            cur.execute(query, args); flights = cur.fetchall(); cur.close(); conn.close(); return flights
        except Error as e: messagebox.showerror("DB", str(e)); return []

    def _do_search_flights(self):
        self._user_flights(search_params={
            "dep": self._s_dep_widget.get(), "dst": self._s_dst_widget.get(),
            "date": self._s_date_proxy.get().strip(), "pax": self._s_pax.get().strip() or 1,
        })

    def _clear_search(self): self._user_flights()

    def _build_flight_card(self, parent, canvas_c, fid, fname, fnum,
                            dep, dst, dep_iata, dst_iata,
                            dep_t, arr_t, dur, cost, total_seats, avail_seats, img_path):
        card = tk.Frame(parent, bg=CARD, cursor="hand2",
                        highlightthickness=2, highlightbackground=BORDER)
        card.pack(fill="x", pady=5)

        def _book(event=None):
            self._bk = {"flight_id":fid,"flight_name":fname,"flight_num":fnum,
                         "departure":dep,"destination":dst,"dep_iata":dep_iata,"arr_iata":dst_iata,
                         "dep_time":dep_t,"arr_time":arr_t,"duration":dur,
                         "cost":cost,"seat":None,"image_path":img_path}
            self._bk_step1_passenger_info()

        card.bind("<Button-1>", _book)
        img_panel = tk.Frame(card, bg=INPUT_BG, width=190, height=130)
        img_panel.pack(side="left"); img_panel.pack_propagate(False)
        img_panel.bind("<Button-1>", _book)
        img_shown = False
        if img_path and os.path.isfile(img_path):
            try:
                from PIL import Image, ImageTk
                im = Image.open(img_path); im.thumbnail((188,126), Image.LANCZOS)
                photo = ImageTk.PhotoImage(im); self._img_cache[f"card_{fid}"] = photo
                il = tk.Label(img_panel, image=photo, bg=INPUT_BG); il.pack(expand=True)
                il.bind("<Button-1>", _book); img_shown = True
            except: pass
        if not img_shown:
            tk.Label(img_panel, text="✈", font=("Segoe UI",38), bg=INPUT_BG, fg=ACCENT).pack(expand=True)

        info = tk.Frame(card, bg=CARD); info.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        info.bind("<Button-1>", _book)
        top_row = tk.Frame(info, bg=CARD); top_row.pack(fill="x"); top_row.bind("<Button-1>", _book)
        tk.Label(top_row, text=fname, font=FH3, bg=CARD, fg=WHITE, cursor="hand2").pack(side="left")
        tk.Label(top_row, text=f"  {fnum}  ", font=FS, bg=ACCENT2, fg=WHITE, padx=6, pady=2).pack(side="left", padx=8)
        tk.Label(top_row, text="  NON-STOP  ", font=FS, bg=SUCCESS, fg=DARK_TEXT, padx=4, pady=2).pack(side="left", padx=4)
        avail_col = SUCCESS if avail_seats > 10 else (WARNING if avail_seats > 0 else DANGER)
        tk.Label(top_row, text=f"  {avail_seats} seats  ", font=FS, bg=avail_col, fg=DARK_TEXT, padx=6, pady=2).pack(side="right", padx=4)
        route_row = tk.Frame(info, bg=CARD); route_row.pack(fill="x", pady=(4,0)); route_row.bind("<Button-1>", _book)
        iata_txt = f"{dep_iata or dep[:3].upper()}  →  {dst_iata or dst[:3].upper()}"
        tk.Label(route_row, text=iata_txt, font=("Segoe UI",20,"bold"), bg=CARD, fg=ACCENT, cursor="hand2").pack(side="left")
        tk.Label(route_row, text=f"  {dep}  →  {dst}", font=FS, bg=CARD, fg=GREY).pack(side="left", padx=6)
        detail_row = tk.Frame(info, bg=CARD); detail_row.pack(fill="x", pady=(6,0)); detail_row.bind("<Button-1>", _book)
        for icon, val in [("🕐",f"Dep: {dep_t}"),("🕑",f"Arr: {arr_t}"),
                           ("⏱",f"Duration: {dur}"),("💵",f"${cost:.2f} USD"),
                           ("💺",f"{total_seats} seats / {avail_seats} avail")]:
            chip = tk.Frame(detail_row, bg=INPUT_BG); chip.pack(side="left", padx=(0,8), pady=2, ipadx=6, ipady=3)
            chip.bind("<Button-1>", _book)
            tk.Label(chip, text=f"{icon} {val}", font=FS, bg=INPUT_BG, fg=WHITE).pack()
        tk.Button(card, text="✈ BOOK NOW", command=_book, bg=ACCENT2, fg=WHITE,
                  font=("Segoe UI",10,"bold"), relief="flat", cursor="hand2",
                  padx=12, pady=8, activebackground=ACCENT, activeforeground=DARK_TEXT
                  ).pack(side="right", padx=14, pady=14)

    # ════════════════════════════════════════════════════════
    #  STEP 1 — PASSENGER DETAILS
    # ════════════════════════════════════════════════════════
    def _bk_step1_passenger_info(self):
        clear_content(self._content)
        page_header(self._content, "Step 1 of 5 — Passenger Details",
                    "Enter the traveller's name and passport information")
        draw_step_bar(self._content, 1, self.WIZARD_STEPS)
        self._bk_flight_bar(self._content)
        scroll_f = make_scrollable(self._content)
        self._p1 = {}
        saved = self._bk.get("_p1_saved", {})

        self._wizard_section(scroll_f, "👤  Traveller Name")
        rf = tk.Frame(scroll_f, bg=BG); rf.pack(fill="x", padx=32, pady=6)
        for ln, key in [("First Name *","first_name"),("Last Name *","last_name")]:
            col = tk.Frame(rf, bg=BG); col.pack(side="left", padx=(0,24), fill="x", expand=True)
            lbl(col, ln, FL, GREY, BG).pack(anchor="w")
            e = entry_w(col, width=28); e.pack(fill="x"); self._p1[key] = e
        if saved:
            self._p1["first_name"].insert(0, saved.get("first_name",""))
            self._p1["last_name"].insert(0, saved.get("last_name",""))

        self._wizard_section(scroll_f, "🛂  Passport Information")
        rf = tk.Frame(scroll_f, bg=BG); rf.pack(fill="x", padx=32, pady=6)
        col_pp = tk.Frame(rf, bg=BG); col_pp.pack(side="left", padx=(0,24), fill="x", expand=True)
        lbl(col_pp, "Passport Number *", FL, GREY, BG).pack(anchor="w")
        e_pp = entry_w(col_pp, width=28); e_pp.pack(fill="x"); self._p1["passport_no"] = e_pp
        if saved: e_pp.insert(0, saved.get("passport_no",""))
        col_exp = tk.Frame(rf, bg=BG); col_exp.pack(side="left", padx=(0,24), fill="x", expand=True)
        exp_f, self._p1_exp_proxy = make_calendar_picker(col_exp, "Passport Expiry Date *", bg=BG)
        exp_f.pack(fill="x")
        if saved and saved.get("passport_exp"): self._p1_exp_proxy.set(saved["passport_exp"])

        self._wizard_section(scroll_f, "🌍  Country of Issue")
        country_rf = tk.Frame(scroll_f, bg=BG); country_rf.pack(fill="x", padx=32, pady=6)
        lbl(country_rf, "Issue Country *", FL, GREY, BG).pack(anchor="w")
        self._p1_country = CountryPicker(country_rf, bg=BG); self._p1_country.pack(anchor="w")
        if saved and saved.get("issue_country"): self._p1_country.set(saved["issue_country"])

        info_f = card_f(scroll_f); info_f.pack(fill="x", padx=32, pady=(10,4), ipadx=14, ipady=10)
        lbl(info_f, "ℹ  Please ensure passport details exactly match your travel document.", FS, GREY, CARD).pack(anchor="w", padx=12)
        lbl(info_f, "   Passport must be valid for at least 6 months from the travel date.", FS, GREY, CARD).pack(anchor="w", padx=12)

        nav_f = tk.Frame(scroll_f, bg=BG); nav_f.pack(anchor="w", padx=32, pady=(16,40))
        btn_w(nav_f, "← Back to Flights", self._user_flights, w=20).pack(side="left", padx=(0,10))
        btn_w(nav_f, "Next: Contact Details →", self._bk_goto_step2,
              bg=SUCCESS, fg=DARK_TEXT, w=28, font=FH3).pack(side="left")

    def _bk_goto_step2(self):
        v = {k: e.get().strip() for k, e in self._p1.items()}
        v["passport_exp"] = self._p1_exp_proxy.get(); v["issue_country"] = self._p1_country.get()
        if not v["first_name"] or not v["last_name"]:
            messagebox.showwarning("Missing","Please enter first and last name."); return
        if not v["passport_no"]: messagebox.showwarning("Missing","Please enter passport number."); return
        if not v["passport_exp"]: messagebox.showwarning("Missing","Please select passport expiry date."); return
        try:
            pexp = datetime.strptime(v["passport_exp"], "%Y-%m-%d").date()
            if pexp <= date.today(): messagebox.showerror("Passport","Passport is expired."); return
        except ValueError: messagebox.showerror("Format","Passport expiry date is invalid."); return
        if not v["issue_country"]: messagebox.showwarning("Country","Please select issue country."); return
        self._bk["_p1_saved"] = v
        self._bk.update({"pax_first_name":v["first_name"],"pax_last_name":v["last_name"],
                          "passport_no":v["passport_no"],"passport_exp":v["passport_exp"],
                          "issue_country":v["issue_country"]})
        self._bk_step2_contact()

    # ════════════════════════════════════════════════════════
    #  STEP 2 — CONTACT DETAILS
    # ════════════════════════════════════════════════════════
    def _bk_step2_contact(self):
        clear_content(self._content)
        page_header(self._content, "Step 2 of 5 — Contact Details",
                    "We'll send your booking confirmation and e-ticket to these details")
        draw_step_bar(self._content, 2, self.WIZARD_STEPS)
        self._bk_flight_bar(self._content)
        scroll_f = make_scrollable(self._content)
        saved = self._bk.get("_p2_saved", {}); self._p2 = {}

        self._wizard_section(scroll_f, "📧  Email Address")
        rf_em = tk.Frame(scroll_f, bg=BG); rf_em.pack(fill="x", padx=32, pady=6)
        lbl(rf_em, "Email Address *", FL, GREY, BG).pack(anchor="w")
        e_em = entry_w(rf_em, width=40); e_em.pack(anchor="w"); self._p2["email"] = e_em
        lbl(rf_em, "Your e-ticket and booking confirmation will be sent here.", FS, GREY, BG).pack(anchor="w", pady=(3,0))
        if saved: e_em.insert(0, saved.get("email",""))

        self._wizard_section(scroll_f, "📱  Mobile Number")
        rf_mob = tk.Frame(scroll_f, bg=BG); rf_mob.pack(fill="x", padx=32, pady=6)
        lbl(rf_mob, "Mobile Number *  (include country code, e.g. +91 98765 43210)", FL, GREY, BG).pack(anchor="w")
        e_mob = entry_w(rf_mob, width=28); e_mob.pack(anchor="w"); self._p2["mobile"] = e_mob
        lbl(rf_mob, "Used for flight alerts and OTP verification.", FS, GREY, BG).pack(anchor="w", pady=(3,0))
        if saved: e_mob.insert(0, saved.get("mobile",""))

        self._wizard_section(scroll_f, "✅  Passenger Details Summary")
        sum_card = card_f(scroll_f); sum_card.pack(fill="x", padx=32, pady=6, ipadx=14, ipady=10)
        p1 = self._bk
        for label_t, val in [("Passenger Name", f"{p1.get('pax_first_name','')} {p1.get('pax_last_name','')}"),
                               ("Passport Number", p1.get("passport_no","—")),
                               ("Passport Expiry", p1.get("passport_exp","—")),
                               ("Issue Country",   p1.get("issue_country","—"))]:
            r = tk.Frame(sum_card, bg=CARD); r.pack(fill="x", padx=10, pady=2)
            lbl(r, label_t, FS, GREY, CARD, width=22).pack(side="left")
            lbl(r, val, FB, WHITE, CARD).pack(side="left", padx=8)

        info_f = card_f(scroll_f); info_f.pack(fill="x", padx=32, pady=(10,4), ipadx=14, ipady=10)
        lbl(info_f, "ℹ  Your contact details are used only for this booking.", FS, GREY, CARD).pack(anchor="w", padx=12)
        lbl(info_f, "   KVK Flyzz will never share your information with third parties.", FS, GREY, CARD).pack(anchor="w", padx=12)

        nav_f = tk.Frame(scroll_f, bg=BG); nav_f.pack(anchor="w", padx=32, pady=(16,40))
        btn_w(nav_f, "← Back to Passenger", self._bk_step1_passenger_info, w=22).pack(side="left", padx=(0,10))
        btn_w(nav_f, "Next: Choose Seat →", self._bk_goto_step3,
              bg=SUCCESS, fg=DARK_TEXT, w=26, font=FH3).pack(side="left")

    def _bk_goto_step3(self):
        email = self._p2["email"].get().strip(); mobile = self._p2["mobile"].get().strip()
        if not email: messagebox.showwarning("Missing","Please enter your email address."); return
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Email","Please enter a valid email address."); return
        if not mobile: messagebox.showwarning("Missing","Please enter your mobile number."); return
        if not re.match(r"^\+?[\d\s\-]{7,15}$", mobile):
            messagebox.showerror("Mobile","Please enter a valid mobile number."); return
        self._bk["_p2_saved"] = {"email":email,"mobile":mobile}
        self._bk["email"] = email; self._bk["mobile"] = mobile
        self._bk_step3_seat()

    # ════════════════════════════════════════════════════════
    #  STEP 3 — SEAT SELECTION
    # ════════════════════════════════════════════════════════
    def _bk_step3_seat(self):
        clear_content(self._content)
        bk = self._bk
        dep_iata = bk.get("dep_iata","") or bk["departure"][:3].upper()
        arr_iata = bk.get("arr_iata","") or bk["destination"][:3].upper()
        page_header(self._content, "Step 3 of 5 — Choose Your Seat",
                    f"{bk['flight_name']}  ({bk['flight_num']})  |  {dep_iata} → {arr_iata}  |  {bk['dep_time']}")
        draw_step_bar(self._content, 3, self.WIZARD_STEPS)

        if bk.get("image_path") and os.path.isfile(bk["image_path"]):
            try:
                from PIL import Image, ImageTk
                banner_frame = tk.Frame(self._content, bg=BG); banner_frame.pack(fill="x", padx=32, pady=(0,8))
                im = Image.open(bk["image_path"]); im.thumbnail((860,110), Image.LANCZOS)
                photo = ImageTk.PhotoImage(im); self._img_cache["banner"] = photo
                tk.Label(banner_frame, image=photo, bg=BG).pack(anchor="w")
            except: pass

        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("SELECT total_seats FROM flights WHERE id=%s", (bk["flight_id"],))
            row = cur.fetchone(); total_seats = int(row[0]) if row else 180
            cur.execute("SELECT seat FROM bookings WHERE flight_id=%s AND is_deleted=0", (bk["flight_id"],))
            booked_seats = {r[0] for r in cur.fetchall()}; cur.close(); conn.close()
        except Error as e: messagebox.showerror("DB", str(e)); return

        avail = total_seats - len(booked_seats)
        SEAT_COLS = ["A","B","C","D","E","F"]
        ROWS = max(math.ceil(total_seats/6), 1)

        stat_row = tk.Frame(self._content, bg=BG); stat_row.pack(fill="x", padx=32, pady=(0,4))
        for txt, val, col in [("Total Seats",total_seats,WHITE),("Booked",len(booked_seats),DANGER),("Available",avail,SUCCESS)]:
            lbl(stat_row, f"{txt}: {val}", FH3, col, BG).pack(side="left", padx=14)
        legend = tk.Frame(self._content, bg=BG); legend.pack(anchor="w", padx=32, pady=(0,4))
        for txt, col in [("■ Available",SUCCESS),("■ Booked",DANGER),("■ Selected",WARNING),
                          ("A/F = Window","#63B3ED"),("B/E = Middle",GREY),("C/D = Aisle","#9AE6B4")]:
            lbl(legend, txt+"   ", FS, col, BG).pack(side="left")

        map_outer = tk.Frame(self._content, bg=BG); map_outer.pack(fill="both", expand=True, padx=32, pady=4)
        left_panel = tk.Frame(map_outer, bg=BG); left_panel.pack(side="left", fill="both", expand=True)
        right_panel = tk.Frame(map_outer, bg=CARD, width=240, highlightthickness=1, highlightbackground=BORDER)
        right_panel.pack(side="right", fill="y", padx=(12,0)); right_panel.pack_propagate(False)

        lbl(right_panel, "Selected Seat", FH3, ACCENT, CARD).pack(anchor="w", padx=12, pady=(16,4))
        self._sel_seat_lbl = lbl(right_panel, "  —  ", ("Segoe UI",32,"bold"), ACCENT, CARD, "center")
        self._sel_seat_lbl.pack(anchor="w", padx=12)
        self._sel_class_lbl = lbl(right_panel, "", FS, GREY, CARD, "center"); self._sel_class_lbl.pack(anchor="w", padx=12, pady=(0,8))
        tk.Frame(right_panel, bg=BORDER, height=1).pack(fill="x", padx=12)
        lbl(right_panel, "Seat Features:", FL, GREY, CARD).pack(anchor="w", padx=12, pady=(8,2))
        self._sel_feat_lbl = lbl(right_panel, "", FS, GREY, CARD, "w", wraplength=200); self._sel_feat_lbl.pack(anchor="w", padx=12)
        tk.Frame(right_panel, bg=BORDER, height=1).pack(fill="x", padx=12, pady=8)
        btn_w(right_panel, "Auto-Assign Best", self._auto_assign_seat, w=20, bg=ACCENT2).pack(padx=12, pady=4)
        btn_w(right_panel, "← Back", self._bk_step2_contact, w=20, bg=PANEL).pack(padx=12, pady=4)
        btn_w(right_panel, "Next: Meal →", self._bk_goto_step4, bg=SUCCESS, fg=DARK_TEXT, w=20, font=FH3).pack(padx=12, pady=4)

        SZ = 36; GAP = 4; AISLE = 20; LABEL_W = 40; COLS_PER_SIDE = 3
        MAP_W = LABEL_W + COLS_PER_SIDE*(SZ+GAP) + AISLE + COLS_PER_SIDE*(SZ+GAP) + 20
        MAP_H = 50 + ROWS*(SZ+GAP) + 20

        can_wrap = tk.Frame(left_panel, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        can_wrap.pack(fill="both", expand=True)
        seat_canvas = tk.Canvas(can_wrap, bg=CARD, highlightthickness=0, width=min(MAP_W,700))
        vsb_seat = ttk.Scrollbar(can_wrap, orient="vertical", command=seat_canvas.yview, style="KVK.Vertical.TScrollbar")
        seat_canvas.configure(yscrollcommand=vsb_seat.set, scrollregion=(0,0,MAP_W,MAP_H))
        seat_canvas.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        vsb_seat.pack(side="right", fill="y")
        seat_canvas.bind("<Enter>", lambda e: seat_canvas.bind_all("<MouseWheel>",
            lambda ev: seat_canvas.yview_scroll(int(-1*(ev.delta/120)),"units")))
        seat_canvas.bind("<Leave>", lambda e: seat_canvas.unbind_all("<MouseWheel>"))

        self._seat_items = {}; self._seat_canvas_avail_colors = {}
        seat_canvas.create_text(MAP_W//2, 14, text="✈  FRONT OF AIRCRAFT", font=("Segoe UI",8,"bold"), fill=ACCENT)
        for ci, col_ltr in enumerate(SEAT_COLS):
            x = LABEL_W+ci*(SZ+GAP)+SZ//2 if ci < 3 else LABEL_W+COLS_PER_SIDE*(SZ+GAP)+AISLE+(ci-3)*(SZ+GAP)+SZ//2
            hdr_col = "#63B3ED" if col_ltr in ("A","F") else (GREY if col_ltr in ("B","E") else "#9AE6B4")
            seat_canvas.create_text(x, 32, text=col_ltr, font=("Segoe UI",9,"bold"), fill=hdr_col)
        seat_canvas.create_text(LABEL_W+COLS_PER_SIDE*(SZ+GAP)+AISLE//2, 32, text="✈", font=("Segoe UI",7), fill=GREY)

        Y0 = 44
        for row_i in range(ROWS):
            row_num = row_i+1; y = Y0+row_i*(SZ+GAP)
            seat_canvas.create_text(LABEL_W//2, y+SZ//2, text=str(row_num), font=("Segoe UI",8,"bold"), fill=GREY)
            if row_num == 5:
                seat_canvas.create_line(LABEL_W, y-2, MAP_W-10, y-2, fill=WARNING, width=1, dash=(4,3))
                seat_canvas.create_text(MAP_W-12, y+6, text="Economy →", font=FS, fill=WARNING, anchor="e")
            for ci, col_ltr in enumerate(SEAT_COLS):
                sn = f"{row_num}{col_ltr}"
                x = LABEL_W+ci*(SZ+GAP) if ci < 3 else LABEL_W+COLS_PER_SIDE*(SZ+GAP)+AISLE+(ci-3)*(SZ+GAP)
                if row_i*6+ci >= total_seats: continue
                is_booked = sn in booked_seats
                avail_col = "#2D6A9F" if col_ltr in ("A","F") else ("#1E4060" if col_ltr in ("B","E") else "#1A5C3A")
                fill = DANGER if is_booked else (WARNING if sn == bk.get("seat") else avail_col)
                tag = f"seat_{sn}"
                rid = seat_canvas.create_rectangle(x, y, x+SZ, y+SZ, fill=fill,
                    outline="#0A1628" if is_booked else BORDER, width=1, tags=tag)
                seat_canvas.create_rectangle(x+2, y, x+SZ-2, y+6,
                    fill="#0A1628" if is_booked else "#0A2040", outline="", tags=tag)
                tid = seat_canvas.create_text(x+SZ//2, y+SZ//2+2, text=sn,
                    font=("Segoe UI",7,"bold"),
                    fill="#888" if is_booked else (DARK_TEXT if sn == bk.get("seat") else WHITE), tags=tag)
                self._seat_items[sn] = (rid, tid, is_booked)
                if not is_booked:
                    def _bind_seat(s=sn, ac=avail_col):
                        seat_canvas.tag_bind(f"seat_{s}", "<Button-1>",
                            lambda e, seat=s, cv=seat_canvas, a=ac: self._pick_seat_airline(cv, seat, a))
                        seat_canvas.tag_bind(f"seat_{s}", "<Enter>", lambda e: seat_canvas.config(cursor="hand2"))
                        seat_canvas.tag_bind(f"seat_{s}", "<Leave>", lambda e: seat_canvas.config(cursor=""))
                    _bind_seat()

        seat_canvas.configure(scrollregion=(0,0,MAP_W,MAP_H))
        self._seat_canvas = seat_canvas
        if bk.get("seat") and bk["seat"] in self._seat_items:
            sn = bk["seat"]; row_num = int(''.join(filter(str.isdigit,sn))); col_ltr = ''.join(filter(str.isalpha,sn))
            self._sel_seat_lbl.config(text=sn, fg=WARNING)
            self._sel_class_lbl.config(text="Business Class" if row_num<=4 else "Economy Class",
                                        fg=WARNING if row_num<=4 else ACCENT)
            pos = ("Window Seat — great views!" if col_ltr in ("A","F") else
                   ("Middle Seat" if col_ltr in ("B","E") else "Aisle Seat — easy access"))
            self._sel_feat_lbl.config(text=pos)

    def _pick_seat_airline(self, canvas, sn, avail_col):
        prev = self._bk.get("seat")
        if prev and prev in self._seat_items:
            rid, tid, _ = self._seat_items[prev]
            canvas.itemconfig(rid, fill=self._seat_canvas_avail_colors.get(prev,"#1E4060"))
            canvas.itemconfig(tid, fill=WHITE)
        self._seat_canvas_avail_colors[sn] = avail_col; self._bk["seat"] = sn
        rid, tid, _ = self._seat_items[sn]
        canvas.itemconfig(rid, fill=WARNING); canvas.itemconfig(tid, fill=DARK_TEXT)
        row_num = int(''.join(filter(str.isdigit,sn))); col_ltr = ''.join(filter(str.isalpha,sn))
        self._sel_seat_lbl.config(text=sn, fg=WARNING)
        self._sel_class_lbl.config(text="Business Class" if row_num<=4 else "Economy Class",
                                    fg=WARNING if row_num<=4 else ACCENT)
        pos = ("Window Seat — great views!" if col_ltr in ("A","F") else
               ("Middle Seat" if col_ltr in ("B","E") else "Aisle Seat — easy access"))
        self._sel_feat_lbl.config(text=pos)
        total_rows = max([int(''.join(filter(str.isdigit,s))) for s in self._seat_items.keys()] or [1])
        canvas.yview_moveto(max(0, (row_num-1)/max(total_rows,1)-0.15))

    def _auto_assign_seat(self):
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("SELECT total_seats FROM flights WHERE id=%s", (self._bk["flight_id"],))
            total = int(cur.fetchone()[0])
            cur.execute("SELECT seat FROM bookings WHERE flight_id=%s AND is_deleted=0", (self._bk["flight_id"],))
            booked = {r[0] for r in cur.fetchall()}; cur.close(); conn.close()
        except: return
        ROWS = math.ceil(total/6)
        SEAT_COLS = ["A","B","C","D","E","F"]
        for pref_col in ["A","F","C","D","B","E"]:
            for row_i in range(ROWS):
                sn = f"{row_i+1}{pref_col}"
                if row_i*6+SEAT_COLS.index(pref_col) < total and sn not in booked and sn in self._seat_items:
                    avail_col = "#2D6A9F" if pref_col in ("A","F") else ("#1A5C3A" if pref_col in ("C","D") else "#1E4060")
                    self._pick_seat_airline(self._seat_canvas, sn, avail_col); return
        messagebox.showinfo("Full","No seats available!")

    def _bk_goto_step4(self):
        if not self._bk.get("seat"): messagebox.showwarning("Seat","Please select a seat first."); return
        self._bk_step4_meal()

    # ════════════════════════════════════════════════════════
    #  STEP 4 — MEAL & BAGGAGE
    # ════════════════════════════════════════════════════════
    def _bk_step4_meal(self):
        clear_content(self._content)
        page_header(self._content, "Step 4 of 5 — Meal & Baggage",
                    "Select your in-flight meal preference and any extra baggage")
        draw_step_bar(self._content, 4, self.WIZARD_STEPS)
        self._bk_flight_bar(self._content)
        scroll_f = make_scrollable(self._content)

        MEAL_OPTIONS = [
            ("No Select",              "✈",  "Standard complimentary meal served on board"),
            ("Complimentary Standard", "🍱", "Full complimentary meal — standard airline offering"),
            ("Vegetarian",             "🥗", "Fresh vegetarian meal — no meat or seafood"),
            ("Vegan",                  "🌱", "100% plant-based, no dairy or animal products"),
            ("Halal",                  "🥩", "Halal-certified meat, prepared per Islamic guidelines"),
            ("Jain",                   "🙏", "Strictly Jain — no root vegetables, no eggs"),
            ("Low-Sodium",             "🧂", "Reduced salt meal for health-conscious travellers"),
            ("Diabetic",               "💉", "Controlled carbohydrates, diabetic-friendly"),
            ("Gluten-Free",            "🌾", "No wheat, barley, or gluten-containing ingredients"),
        ]
        saved_meal = self._bk.get("meal_pref","No Select")
        self._meal_var = tk.StringVar(value=saved_meal)

        self._wizard_section(scroll_f, "🍽  In-Flight Meal Preference")
        meal_grid = tk.Frame(scroll_f, bg=BG); meal_grid.pack(fill="x", padx=32, pady=8)
        for idx, (meal_name, emoji, desc) in enumerate(MEAL_OPTIONS):
            row_i, col_i = divmod(idx, 3)
            cell = tk.Frame(meal_grid, bg=CARD, highlightthickness=2, highlightbackground=BORDER)
            cell.grid(row=row_i, column=col_i, padx=6, pady=6, sticky="nsew", ipadx=8, ipady=8)
            meal_grid.columnconfigure(col_i, weight=1)

            def _make_select(mn=meal_name, fr=cell):
                def _select():
                    self._meal_var.set(mn)
                    for w in meal_grid.winfo_children(): w.configure(highlightbackground=BORDER)
                    fr.configure(highlightbackground=ACCENT)
                return _select
            sel_fn = _make_select()
            tk.Label(cell, text=emoji, font=("Segoe UI",22), bg=CARD, fg=WHITE).pack(pady=(6,2))
            tk.Label(cell, text=meal_name, font=FL, bg=CARD, fg=WHITE).pack()
            tk.Label(cell, text=desc, font=FS, bg=CARD, fg=GREY, wraplength=180, justify="center").pack(pady=(2,6))
            tk.Radiobutton(cell, variable=self._meal_var, value=meal_name,
                           bg=CARD, fg=GREY, selectcolor=ACCENT2, activebackground=CARD,
                           font=FS, indicatoron=1, relief="flat", command=sel_fn).pack(pady=(0,4))
            cell.bind("<Button-1>", lambda e, f=sel_fn: f())
            if meal_name == saved_meal: cell.configure(highlightbackground=ACCENT)

        self._wizard_section(scroll_f, "🧳  Baggage Allowance")
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("SELECT luggage_kg FROM flights WHERE id=%s", (self._bk["flight_id"],))
            lug_kg = cur.fetchone()[0]; cur.close(); conn.close()
        except: lug_kg = 30
        self._bk["luggage_kg"] = lug_kg

        bag_info = card_f(scroll_f); bag_info.pack(fill="x", padx=32, pady=6, ipadx=14, ipady=10)
        for icon, label_t, val, col in [
            ("🧳","Checked Baggage (included)",f"{lug_kg} kg per passenger",SUCCESS),
            ("💼","Hand / Cabin Baggage (included)","7 kg (standard)",SUCCESS),
            ("💰","Excess Baggage Rate","$8.00 USD per kg",WARNING),
        ]:
            r = tk.Frame(bag_info, bg=CARD); r.pack(fill="x", padx=10, pady=3)
            lbl(r, f"{icon}  {label_t}", FB, GREY, CARD, width=36).pack(side="left")
            lbl(r, val, FL, col, CARD).pack(side="left", padx=8)

        ex_f = tk.Frame(scroll_f, bg=BG); ex_f.pack(fill="x", padx=32, pady=6)
        lbl(ex_f, "Extra Checked Baggage — additional kg required (enter 0 if none):", FL, GREY, BG).pack(anchor="w")
        ex_row = tk.Frame(ex_f, bg=BG); ex_row.pack(anchor="w", pady=4)
        self._excess_var = tk.StringVar(value=str(self._bk.get("excess_kg",0)))
        tk.Spinbox(ex_row, from_=0, to=50, width=6, textvariable=self._excess_var,
                   bg=INPUT_BG, fg=WHITE, font=FH3, buttonbackground=BORDER,
                   relief="flat", insertbackground=ACCENT, wrap=False).pack(side="left", ipady=6)
        self._excess_cost_lbl = lbl(ex_row, "", FB, WARNING, BG); self._excess_cost_lbl.pack(side="left", padx=14)

        def _update_excess(*args):
            try:
                kg = int(self._excess_var.get() or 0)
                self._excess_cost_lbl.config(
                    text=f"= ${kg*8.0:.2f} USD excess baggage charge" if kg > 0 else "No excess baggage charge")
            except: pass
        self._excess_var.trace("w", _update_excess); _update_excess()

        self._wizard_section(scroll_f, "📋  Booking Summary So Far")
        sum_c = card_f(scroll_f); sum_c.pack(fill="x", padx=32, pady=6, ipadx=14, ipady=10)
        bk = self._bk
        for label_t, val in [("Passenger",f"{bk.get('pax_first_name','')} {bk.get('pax_last_name','')}"),
                               ("Passport No.",bk.get("passport_no","—")),("Issue Country",bk.get("issue_country","—")),
                               ("Email",bk.get("email","—")),("Mobile",bk.get("mobile","—")),("Seat",bk.get("seat","—"))]:
            r = tk.Frame(sum_c, bg=CARD); r.pack(fill="x", padx=10, pady=2)
            lbl(r, label_t, FS, GREY, CARD, width=20).pack(side="left")
            lbl(r, val, FB, WHITE, CARD).pack(side="left", padx=8)

        nav_f = tk.Frame(scroll_f, bg=BG); nav_f.pack(anchor="w", padx=32, pady=(16,40))
        btn_w(nav_f, "← Back to Seat Map", self._bk_step3_seat, w=22).pack(side="left", padx=(0,10))
        btn_w(nav_f, "Next: Payment →", self._bk_goto_step5,
              bg=SUCCESS, fg=DARK_TEXT, w=26, font=FH3).pack(side="left")

    def _bk_goto_step5(self):
        meal = self._meal_var.get() if hasattr(self,"_meal_var") else "No Select"
        try: excess = max(int(self._excess_var.get() or 0), 0)
        except: excess = 0
        self._bk["meal_pref"] = meal; self._bk["excess_kg"] = excess
        self._bk_step5_payment()

    # ════════════════════════════════════════════════════════
    #  STEP 5 — PAYMENT  (summary pinned above scroll area)
    # ════════════════════════════════════════════════════════
    def _bk_step5_payment(self):
        clear_content(self._content)
        page_header(self._content, "Step 5 of 5 — Payment",
                    "Review your booking and complete payment")
        draw_step_bar(self._content, 5, self.WIZARD_STEPS)
        self._bk_flight_bar(self._content)

        # ── PINNED: Currency + Payment Summary (always visible, never scrolls away) ──
        pinned = tk.Frame(self._content, bg=BG)
        pinned.pack(fill="x", padx=32, pady=(0, 4))

        # Currency row
        cur_row_f = tk.Frame(pinned, bg=BG); cur_row_f.pack(fill="x")
        lbl(cur_row_f, "💱  Payment Currency:", FL, ACCENT, BG).pack(side="left", padx=(0, 8))
        self._cur_var = tk.StringVar(value=self._selected_currency)
        for code, info in CURRENCIES.items():
            tk.Radiobutton(cur_row_f, text=f"{info['symbol']} {code}",
                           variable=self._cur_var, value=code,
                           bg=BG, fg=GREY, selectcolor=ACCENT2,
                           activebackground=BG, activeforeground=ACCENT,
                           font=("Segoe UI", 10, "bold"), indicatoron=0,
                           relief="flat", padx=10, pady=6, cursor="hand2",
                           width=8).pack(side="left", padx=3)
        self._cur_rate_lbl = lbl(pinned, "", FS, GREY, BG); self._cur_rate_lbl.pack(anchor="w", pady=(2, 4))

        # Payment summary card (pinned)
        self._pay_card = card_f(pinned); self._pay_card.pack(fill="x", pady=(0, 4), ipadx=16, ipady=8)

        # Agreement + big Confirm button (pinned)
        agree_f = tk.Frame(pinned, bg=BG); agree_f.pack(fill="x", pady=(4, 2))
        self._agree_var = tk.BooleanVar()
        tk.Checkbutton(agree_f, text="  I have reviewed all booking details and agree to KVK Flyzz terms & conditions",
                       variable=self._agree_var, bg=BG, fg=WHITE, selectcolor=INPUT_BG,
                       activebackground=BG, font=FB, cursor="hand2").pack(anchor="w")
        pay_btn_f = tk.Frame(pinned, bg=BG); pay_btn_f.pack(fill="x", pady=(4, 6))
        self._confirm_btn = tk.Button(pay_btn_f, text="✅   CONFIRM & PAY NOW",
                                      command=self._do_confirm_booking,
                                      bg=SUCCESS, fg=DARK_TEXT, font=("Segoe UI", 14, "bold"),
                                      relief="flat", cursor="hand2", padx=24, pady=14,
                                      activebackground=ACCENT, activeforeground=DARK_TEXT)
        self._confirm_btn.pack(side="left")

        tk.Frame(self._content, bg=BORDER, height=1).pack(fill="x", padx=32, pady=(0, 4))

        # ── SCROLLABLE: Booking review + notices + back button ──
        scroll_f = make_scrollable(self._content)

        # Booking review grid
        lbl(scroll_f, "📋  Complete Booking Review", FH3, ACCENT, BG).pack(anchor="w", padx=32, pady=(14,2))
        tk.Frame(scroll_f, bg=BORDER, height=1).pack(fill="x", padx=32, pady=2)
        review_card = card_f(scroll_f); review_card.pack(fill="x", padx=32, pady=6, ipadx=16, ipady=12)
        bk = self._bk
        dep_iata = bk.get("dep_iata","") or bk["departure"][:3].upper()
        arr_iata = bk.get("arr_iata","") or bk["destination"][:3].upper()
        review_items = [
            ("Flight",          f"{bk.get('flight_name','')}  ({bk.get('flight_num','')})"),
            ("Route",           f"{dep_iata} ({bk['departure']}) → {arr_iata} ({bk['destination']})"),
            ("Departure",       bk.get("dep_time","—")),
            ("Arrival",         bk.get("arr_time","—")),
            ("Duration",        bk.get("duration","—")),
            ("Passenger Name",  f"{bk.get('pax_first_name','')} {bk.get('pax_last_name','')}"),
            ("Passport No.",    bk.get("passport_no","—")),
            ("Passport Expiry", bk.get("passport_exp","—")),
            ("Issue Country",   bk.get("issue_country","—")),
            ("Email",           bk.get("email","—")),
            ("Mobile",          bk.get("mobile","—")),
            ("Seat",            bk.get("seat","—")),
            ("Meal",            bk.get("meal_pref","No Select")),
            ("Checked Baggage", f"{bk.get('luggage_kg',30)} kg (incl.) + {bk.get('excess_kg',0)} kg extra"),
        ]
        grid_f = tk.Frame(review_card, bg=CARD); grid_f.pack(fill="x", padx=10, pady=4)
        for i, (label_t, val) in enumerate(review_items):
            row_i, col_i = divmod(i, 2)
            cell = tk.Frame(grid_f, bg=INPUT_BG)
            cell.grid(row=row_i, column=col_i, padx=4, pady=3, sticky="nsew", ipadx=8, ipady=6)
            grid_f.columnconfigure(col_i, weight=1)
            lbl(cell, label_t, FS, GREY, INPUT_BG, width=18).pack(side="left")
            lbl(cell, str(val), FB, WHITE, INPUT_BG).pack(side="left", padx=6)

        # Security notice
        notice_f = card_f(scroll_f, bg="#0D1F3A")
        notice_f.pack(fill="x", padx=32, pady=(4,6), ipadx=14, ipady=10)
        tk.Label(notice_f, text="🔒  Secure Payment", font=FH3, bg="#0D1F3A", fg=SUCCESS
                 ).pack(anchor="w", padx=12, pady=(6,2))
        for line in ["• All transactions are processed securely via KVK Flyzz encrypted gateway.",
                     "• Your card details are never stored on our servers.",
                     "• Booking is confirmed instantly upon payment — your e-ticket will be available in My Bookings."]:
            lbl(notice_f, line, FS, GREY, "#0D1F3A").pack(anchor="w", padx=16, pady=1)

        # Nav buttons
        nav_f = tk.Frame(scroll_f, bg=BG); nav_f.pack(anchor="w", padx=32, pady=(6,50))
        btn_w(nav_f, "← Back to Meal & Baggage", self._bk_step4_meal, w=26).pack(side="left", padx=(0,10))
        btn_w(nav_f, "✕  Cancel Booking", self._user_flights, bg=DANGER, w=20).pack(side="left")

        # Wire currency change AFTER all widgets exist
        def _on_cur(*args):
            code = self._cur_var.get(); self._selected_currency = code
            self._cur_rate_lbl.config(text=f"1 USD = {CURRENCIES[code]['rate']} {code}  (indicative rate)")
            self._render_payment_summary()
        self._cur_var.trace("w", _on_cur); _on_cur()

    def _render_payment_summary(self):
        for w in self._pay_card.winfo_children(): w.destroy()
        bk = self._bk
        excess = bk.get("excess_kg", 0); base = float(bk["cost"])
        ex_cost = excess * 8.0; tax = round((base + ex_cost) * 0.09, 2); total = base + ex_cost + tax
        self._bk["excess_cost"] = ex_cost; self._bk["total"] = total
        cur_code = self._cur_var.get() if hasattr(self,"_cur_var") else "USD"
        for label_t, val_usd, col, is_div in [
            ("✈  Base Fare",         base,    WHITE,   False),
            ("🧳  Excess Baggage",   ex_cost, WHITE,   False),
            ("🏦  Taxes & Fees (9%)",tax,     GREY,    False),
            (None, None, BORDER, True),
            ("💳  TOTAL PAYABLE",    total,   SUCCESS, False),
        ]:
            r = tk.Frame(self._pay_card, bg=CARD); r.pack(fill="x", padx=10, pady=2)
            if is_div: tk.Frame(r, bg=BORDER, height=1).pack(fill="x", pady=4); continue
            lbl(r, label_t, FB, GREY, CARD).pack(side="left")
            display = fmt_currency(val_usd, cur_code)
            if cur_code != "USD": display += f"   (${val_usd:.2f} USD)"
            lbl(r, display,
                ("Segoe UI",13,"bold") if "TOTAL" in label_t else FB,
                SUCCESS if "TOTAL" in label_t else col, CARD).pack(side="right")
        if hasattr(self,"_confirm_btn"):
            self._confirm_btn.config(text=f"✅   CONFIRM & PAY  —  {fmt_currency(total, cur_code)} ({cur_code})")

    # ════════════════════════════════════════════════════════
    #  CONFIRM BOOKING
    # ════════════════════════════════════════════════════════
    def _do_confirm_booking(self):
        if not self._agree_var.get():
            messagebox.showwarning("Agreement","Please tick the agreement checkbox before confirming."); return
        bk = self._bk
        for key, label_t in [("pax_first_name","First Name"),("pax_last_name","Last Name"),
                               ("passport_no","Passport Number"),("passport_exp","Passport Expiry"),
                               ("issue_country","Issue Country"),("email","Email"),
                               ("mobile","Mobile"),("seat","Seat")]:
            if not bk.get(key):
                messagebox.showerror("Missing Data",f"'{label_t}' is missing. Please go back and complete all steps.")
                return
        excess = bk.get("excess_kg",0); base = float(bk["cost"])
        ex_cost = excess * 8.0; tax = round((base+ex_cost)*0.09, 2); total = base+ex_cost+tax
        cur_code = self._cur_var.get() if hasattr(self,"_cur_var") else "USD"
        meal = bk.get("meal_pref","No Select")
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("SELECT id FROM bookings WHERE flight_id=%s AND seat=%s AND is_deleted=0",
                        (bk["flight_id"], bk["seat"]))
            if cur.fetchone():
                messagebox.showerror("Seat Taken","This seat was just taken. Please choose another.")
                cur.close(); conn.close(); self._bk_step3_seat(); return
            pnr = _pnr()
            for _ in range(20):
                cur.execute("SELECT id FROM bookings WHERE pnr=%s", (pnr,))
                if not cur.fetchone(): break
                pnr = _pnr()
            cur.execute(
                """INSERT INTO bookings
                   (pnr,user_id,flight_id,seat,pax_first_name,pax_last_name,
                    passport_no,passport_expiry,issue_country,email,mobile,meal_pref,
                    base_fare,excess_baggage_kg,excess_baggage_cost,total_paid,currency_code)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (pnr,self.user_id,bk["flight_id"],bk["seat"],
                 bk["pax_first_name"],bk["pax_last_name"],bk["passport_no"],bk["passport_exp"],
                 bk["issue_country"],bk["email"],bk["mobile"],meal,
                 base,excess,ex_cost,total,cur_code))
            cur.execute("UPDATE flights SET seats_booked=seats_booked+1 WHERE id=%s", (bk["flight_id"],))
            conn.commit(); cur.close(); conn.close()
        except Error as e: messagebox.showerror("DB Error", str(e)); return

        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute("SELECT departure_time,arrival_time,luggage_kg,departure_iata,destination_iata "
                        "FROM flights WHERE id=%s", (bk["flight_id"],))
            dep_dt,arr_dt,lug_kg,db_dep_iata,db_arr_iata = cur.fetchone(); cur.close(); conn.close()
        except: dep_dt = arr_dt = datetime.now(); lug_kg = 30; db_dep_iata = db_arr_iata = ""

        boarding_closes = (dep_dt-timedelta(hours=1)).strftime("%d %b %Y %H:%M")
        dur = _duration_str(dep_dt, arr_dt)
        dep_iata = db_dep_iata or bk.get("dep_iata",""); arr_iata = db_arr_iata or bk.get("arr_iata","")
        dep_r = lookup_iata(dep_iata); arr_r = lookup_iata(arr_iata)
        td = {
            "pnr": pnr, "flight_name": bk["flight_name"], "flight_number": bk["flight_num"],
            "departure": bk["departure"], "destination": bk["destination"],
            "dep_iata": dep_iata, "arr_iata": arr_iata,
            "dep_country": dep_r[2] if dep_r else bk["departure"],
            "arr_country": arr_r[2] if arr_r else bk["destination"],
            "dep_time": dep_dt.strftime("%d %b %Y %H:%M"), "arr_time": arr_dt.strftime("%d %b %Y %H:%M"),
            "duration": dur, "pax_name": f"{bk['pax_first_name']} {bk['pax_last_name']}",
            "passport": bk["passport_no"], "passport_exp": bk["passport_exp"],
            "issue_country": bk["issue_country"], "email": bk["email"], "mobile": bk["mobile"],
            "seat": bk["seat"], "meal_pref": meal, "base_fare": base,
            "excess_kg": excess, "excess_cost": ex_cost, "total_paid": total,
            "currency_code": cur_code, "luggage_kg": lug_kg,
            "booked_date": datetime.now().strftime("%d %b %Y %H:%M"), "boarding_closes": boarding_closes,
        }
        self._bk_step_confirmation(td)

    # ════════════════════════════════════════════════════════
    #  BOOKING CONFIRMATION
    # ════════════════════════════════════════════════════════
    def _bk_step_confirmation(self, td):
        clear_content(self._content)
        page_header(self._content, "✅  Booking Confirmed!", f"PNR: {td['pnr']}  — Your boarding pass is ready.")
        pnr_f = tk.Frame(self._content, bg=SUCCESS); pnr_f.pack(fill="x", padx=32, pady=(0,8), ipadx=16, ipady=12)
        lbl(pnr_f, f"🎫  PNR: {td['pnr']}  |  Flight: {td['flight_number']}  |  "
            f"Seat: {td['seat']}  |  Paid: {fmt_currency(td['total_paid'],td.get('currency_code','USD'))}",
            FH3, DARK_TEXT, SUCCESS, "center").pack()
        self._draw_boarding_pass_preview(tk.Frame(self._content, bg=BG).__class__(self._content, bg=BG), td)
        bp_frame = tk.Frame(self._content, bg=BG); bp_frame.pack(padx=32, pady=4)
        self._draw_boarding_pass_preview(bp_frame, td)
        info_frame = card_f(self._content); info_frame.pack(fill="x", padx=32, pady=(8,4), ipadx=16, ipady=10)
        lbl(info_frame, "📋  Booking Summary", FH3, ACCENT, CARD).pack(anchor="w", padx=16, pady=(10,4))
        tk.Frame(info_frame, bg=BORDER, height=1).pack(fill="x", padx=16, pady=2)
        cur_code = td.get("currency_code","USD")
        paid_f = tk.Frame(info_frame, bg=ACCENT2); paid_f.pack(fill="x", padx=16, pady=6, ipadx=10, ipady=6)
        lbl(paid_f, f"💰  Amount Paid: {fmt_currency(td['total_paid'],cur_code)}  ({cur_code})", FH3, WHITE, ACCENT2).pack(anchor="w", padx=8)
        for line in [
            f"• Route: {td.get('dep_iata','')} ({td.get('dep_country','')}) → {td.get('arr_iata','')} ({td.get('arr_country','')})",
            f"• Departure: {td['dep_time']}  (Terminal 1)   |   Arrival: {td['arr_time']}  (Terminal 2)",
            f"• Duration: {td.get('duration','—')}   |   NON-STOP",
            f"• Seat: {td['seat']}   |   Checked bag: {td['luggage_kg']} kg   |   Hand: 7 kg",
            f"• Meal: {td.get('meal_pref','No Select')}   |   Boarding closes: {td.get('boarding_closes','—')}",
        ]:
            lbl(info_frame, line, FS, GREY, CARD).pack(anchor="w", padx=20, pady=1)
        btn_row = tk.Frame(self._content, bg=BG); btn_row.pack(pady=14, padx=32, anchor="w")
        btn_w(btn_row, "📥  Download PDF Ticket", lambda: self._download_pdf(td),
              bg=SUCCESS, fg=DARK_TEXT, w=26, font=FH3).pack(side="left", padx=(0,12))
        btn_w(btn_row, "✈ Book Another", self._user_flights, w=16).pack(side="left", padx=(0,8))
        btn_w(btn_row, "📋 My Bookings", self._user_bookings, w=16).pack(side="left")

    def _draw_boarding_pass_preview(self, parent, td):
        W, H = 860, 220
        canvas = tk.Canvas(parent, width=W, height=H, bg=BG, highlightthickness=0); canvas.pack()

        def rr(x1, y1, x2, y2, r, fill):
            for args in [(x1,y1,x1+2*r,y1+2*r,90,90),(x2-2*r,y1,x2,y1+2*r,0,90),
                          (x1,y2-2*r,x1+2*r,y2,180,90),(x2-2*r,y2-2*r,x2,y2,270,90)]:
                canvas.create_arc(*args[:4], start=args[4], extent=args[5], style="pieslice", fill=fill, outline=fill)
            canvas.create_rectangle(x1+r,y1,x2-r,y2,fill=fill,outline=fill)
            canvas.create_rectangle(x1,y1+r,x2,y2-r,fill=fill,outline=fill)

        rr(4,4,W-4,H-4,12,"#FFFFFF")
        rr(4,4,W-4,46,12,"#0A2647"); canvas.create_rectangle(4,4,W-4,46,fill="#0A2647",outline="#0A2647")
        canvas.create_text(18,26,text="✈  KVK FLIGHTS FLYZZ",font=("Segoe UI",13,"bold"),fill="white",anchor="w")
        canvas.create_text(W-18,26,text="BOARDING PASS  |  NON-STOP  |  ECONOMY",font=("Segoe UI",8,"bold"),fill="#90CAF9",anchor="e")
        stub_x = W-120
        for y in range(50,H-4,8): canvas.create_oval(stub_x-3,y,stub_x+3,y+4,fill="#BCC8D8",outline="")
        dep_iata = td.get("dep_iata","") or td["departure"][:3].upper()
        arr_iata = td.get("arr_iata","") or td["destination"][:3].upper()
        canvas.create_text(18,86,text=dep_iata,font=("Segoe UI",36,"bold"),fill="#0A2647",anchor="w")
        canvas.create_text(120,80,text=f"→ {td.get('duration','')}",font=("Segoe UI",12),fill="#0077B6",anchor="w")
        canvas.create_text(220,86,text=arr_iata,font=("Segoe UI",36,"bold"),fill="#0A2647",anchor="w")
        canvas.create_text(18,104,text=td["departure"][:22],font=("Segoe UI",7),fill="#888",anchor="w")
        canvas.create_text(220,104,text=td["destination"][:22],font=("Segoe UI",7),fill="#888",anchor="w")
        fields = [("PASSENGER",td["pax_name"]),("FLIGHT",td["flight_number"]),("DATE",td["dep_time"][:11]),
                  ("DEPARTURE",td["dep_time"]),("ARRIVAL",td["arr_time"]),("SEAT",td["seat"]),
                  ("PASSPORT",td["passport"]),("COUNTRY",td["issue_country"][:18]),("PNR",td["pnr"])]
        for i,(lbl_t,val) in enumerate(fields):
            col,row_i = i%3,i//3; x = 18+col*220; y = 120+row_i*26
            canvas.create_text(x,y,text=lbl_t,font=("Segoe UI",6,"bold"),fill="#999",anchor="w")
            canvas.create_text(x,y+12,text=str(val),font=("Segoe UI",8,"bold"),fill="#1A2A4A",anchor="w")
        stub_mid = stub_x+(W-4-stub_x)//2
        canvas.create_rectangle(stub_x+2,4,W-4,H-4,fill="#F0F6FF",outline="#F0F6FF")
        canvas.create_text(stub_mid,68,text="SEAT",font=("Segoe UI",8,"bold"),fill="#0077B6",anchor="center")
        canvas.create_text(stub_mid,92,text=td["seat"],font=("Segoe UI",28,"bold"),fill="#0A2647",anchor="center")
        canvas.create_text(stub_mid,114,text="PNR",font=("Segoe UI",7),fill="#888",anchor="center")
        canvas.create_text(stub_mid,130,text=td["pnr"],font=("Consolas",14,"bold"),fill="#0A2647",anchor="center")
        canvas.create_text(stub_mid,152,text=fmt_currency(td["total_paid"],td.get("currency_code","USD")),
                           font=("Segoe UI",9,"bold"),fill="#0A2647",anchor="center")
        canvas.create_text(stub_mid,H-14,text=td["flight_number"],font=("Segoe UI",8,"bold"),fill="#0077B6",anchor="center")
        canvas.create_rectangle(4,H-30,stub_x-2,H-4,fill="#F0F6FF",outline="#F0F6FF")
        canvas.create_text(18,H-20,
                           text=f"Checked: {td['luggage_kg']}kg  |  Hand: 7kg  |  "
                                f"Meal: {td.get('meal_pref','—')}  |  Boarding: {td.get('boarding_closes','')}",
                           font=("Segoe UI",7),fill="#777",anchor="w")

    def _download_pdf(self, td):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
                                            initialfile=f"KVKFlyzz_Ticket_{td['pnr']}.pdf")
        if not path: return
        try:
            generate_pdf_ticket(td, path)
            messagebox.showinfo("Saved", f"PDF E-Ticket saved:\n{path}\n\n"
                                f"Page 1: Boarding Pass + QR Code\nPage 2: Booking Details & Important Information")
        except Exception as e: messagebox.showerror("PDF Error", str(e))

    # ════════════════════════════════════════════════════════
    #  MY BOOKINGS
    # ════════════════════════════════════════════════════════
    def _user_bookings(self):
        clear_content(self._content)
        page_header(self._content, "My Bookings", f"Logged in as: {self.user_name}")
        cols = ("S.No","PNR","Flight","Route","Departure","Duration","Seat","Currency","Total Paid","Booked On")
        widths = [45,80,110,180,140,80,60,70,110,140]
        tree, tf = make_tree(self._content, cols, widths, height=10)
        tf.pack(fill="x", padx=32, pady=4)
        action_bar = tk.Frame(self._content, bg=BG); action_bar.pack(fill="x", padx=32, pady=(0,8))
        lbl(action_bar, "Select a booking above to download its E-Ticket:", FL, GREY, BG).pack(side="left")
        self._dl_btn = btn_w(action_bar, "📥  Download E-Ticket (PDF)", self._download_selected_ticket,
                              bg=SUCCESS, fg=DARK_TEXT, w=28, font=FH3)
        self._dl_btn.pack(side="left", padx=12); self._dl_btn.config(state="disabled", bg=GREY)

        detail_card = card_f(self._content); detail_card.pack(fill="x", padx=32, pady=(0,12), ipadx=16, ipady=12)
        lbl(detail_card, "Booking Details", FH3, ACCENT, CARD).pack(anchor="w", padx=16, pady=(10,4))
        tk.Frame(detail_card, bg=BORDER, height=1).pack(fill="x", padx=16)
        self._detail_fields = {}
        dg = tk.Frame(detail_card, bg=CARD); dg.pack(fill="x", padx=16, pady=8)
        for i, (label_t, key) in enumerate([("PNR","pnr"),("Flight","flight"),("Route","route"),
                                             ("Seat","seat"),("Departure","dep"),("Arrival","arr"),
                                             ("Duration","dur"),("Paid","paid"),("Meal","meal"),("Baggage","bag")]):
            col_f = tk.Frame(dg, bg=CARD); col_f.grid(row=i//5, column=i%5, padx=12, pady=4, sticky="w")
            lbl(col_f, label_t, FS, GREY, CARD).pack(anchor="w")
            val_lbl = lbl(col_f, "—", FB, WHITE, CARD); val_lbl.pack(anchor="w")
            self._detail_fields[key] = val_lbl

        self._booking_data_cache = {}
        try:
            conn = _conn(); cur = conn.cursor()
            cur.execute(
                """SELECT b.id,b.pnr,f.flight_number,
                          CONCAT(f.departure_area,' → ',f.destination_area),
                          DATE_FORMAT(f.departure_time,'%d %b %Y %H:%i'),
                          DATE_FORMAT(f.arrival_time,'%d %b %Y %H:%i'),
                          f.departure_time,f.arrival_time,
                          b.seat,IFNULL(b.currency_code,'USD'),b.total_paid,
                          DATE_FORMAT(b.booking_date,'%d %b %Y %H:%i'),
                          b.pax_first_name,b.pax_last_name,b.passport_no,b.passport_expiry,b.issue_country,
                          b.email,b.mobile,b.meal_pref,b.base_fare,b.excess_baggage_kg,b.excess_baggage_cost,
                          f.luggage_kg,f.flight_name,f.departure_iata,f.destination_iata,
                          f.departure_area,f.destination_area
                   FROM bookings b JOIN flights f ON b.flight_id=f.id
                   WHERE b.user_id=%s AND b.is_deleted=0 ORDER BY b.booking_date DESC""",
                (self.user_id,))
            rows = cur.fetchall(); cur.close(); conn.close()
        except Error as e: messagebox.showerror("DB", str(e)); return

        for sno, r in enumerate(rows, 1):
            (bid,pnr,fnum,route,dep_t_str,arr_t_str,dep_dt,arr_dt,
             seat,cur_code,total_paid,booked_on,fn,ln,passport,passport_exp,issue_country,
             email,mobile,meal,base_fare,exc_kg,exc_cost,lug_kg,fname,
             dep_iata,arr_iata,dep_area,arr_area) = r
            dur = _duration_str(dep_dt,arr_dt) if dep_dt and arr_dt else "—"
            tree.insert("","end", values=(sno,pnr,fnum,route,dep_t_str,dur,seat,
                                          cur_code,fmt_currency(float(total_paid),cur_code),booked_on), iid=str(bid))
            boarding_closes = (dep_dt-timedelta(hours=1)).strftime("%d %b %Y %H:%M") if dep_dt else "—"
            dep_r = lookup_iata(dep_iata or ""); arr_r = lookup_iata(arr_iata or "")
            self._booking_data_cache[str(bid)] = {
                "pnr":pnr,"flight_name":fname,"flight_number":fnum,"departure":dep_area,"destination":arr_area,
                "dep_iata":dep_iata or "","arr_iata":arr_iata or "",
                "dep_country":dep_r[2] if dep_r else dep_area,"arr_country":arr_r[2] if arr_r else arr_area,
                "dep_time":dep_t_str,"arr_time":arr_t_str,"duration":dur,
                "pax_name":f"{fn} {ln}","passport":passport,"passport_exp":str(passport_exp) if passport_exp else "",
                "issue_country":issue_country,"email":email,"mobile":mobile,"seat":seat,
                "meal_pref":meal or "No Select","base_fare":float(base_fare),
                "excess_kg":int(exc_kg),"excess_cost":float(exc_cost),"total_paid":float(total_paid),
                "currency_code":cur_code,"luggage_kg":int(lug_kg),"booked_date":booked_on,"boarding_closes":boarding_closes,
            }

        def _on_select(event=None):
            sel = tree.selection()
            if not sel: self._dl_btn.config(state="disabled",bg=GREY); return
            data = self._booking_data_cache.get(sel[0],{})
            self._dl_btn.config(state="normal", bg=SUCCESS)
            self._detail_fields["pnr"].config(text=data.get("pnr","—"),fg=ACCENT)
            self._detail_fields["flight"].config(text=data.get("flight_number","—"))
            self._detail_fields["route"].config(text=data.get("departure","")+" → "+data.get("destination",""))
            self._detail_fields["seat"].config(text=data.get("seat","—"),fg=WARNING)
            self._detail_fields["dep"].config(text=data.get("dep_time","—"))
            self._detail_fields["arr"].config(text=data.get("arr_time","—"))
            self._detail_fields["dur"].config(text=data.get("duration","—"))
            cur_code = data.get("currency_code","USD")
            self._detail_fields["paid"].config(text=fmt_currency(data.get("total_paid",0),cur_code)+f" {cur_code}",fg=SUCCESS)
            self._detail_fields["meal"].config(text=data.get("meal_pref","—"))
            self._detail_fields["bag"].config(text=f"{data.get('luggage_kg',30)}kg + 7kg hand")

        tree.bind("<<TreeviewSelect>>", _on_select)
        self._selected_booking_tree = tree

    def _download_selected_ticket(self):
        sel = self._selected_booking_tree.selection()
        if not sel: messagebox.showwarning("Select","Please select a booking first."); return
        td = self._booking_data_cache.get(sel[0])
        if not td: messagebox.showerror("Error","Booking data not found."); return
        self._download_pdf(td)

    def _render_bookings_tree(self, parent, limit=None):
        cols = ("S.No","PNR","Passenger","Flight","Route","Seat","Currency","Paid","Date")
        widths = [45,80,160,90,180,60,60,90,140]
        tree, tf = make_tree(parent, cols, widths, height=8 if limit else 14)
        tf.pack(fill="both", expand=True, padx=32, pady=4)
        try:
            conn = _conn(); cur = conn.cursor()
            q = ("SELECT b.pnr,CONCAT(b.pax_first_name,' ',b.pax_last_name),"
                 "f.flight_number,CONCAT(f.departure_area,' → ',f.destination_area),"
                 "b.seat,IFNULL(b.currency_code,'USD'),b.total_paid,"
                 "DATE_FORMAT(b.booking_date,'%d %b %Y %H:%i') "
                 "FROM bookings b JOIN flights f ON b.flight_id=f.id "
                 "WHERE b.is_deleted=0 ORDER BY b.booking_date DESC")
            if limit: q += f" LIMIT {limit}"
            cur.execute(q)
            for sno, r in enumerate(cur.fetchall(), 1): tree.insert("","end", values=(sno,)+r)
            cur.close(); conn.close()
        except Error as e: messagebox.showerror("DB", str(e))


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        setup_db()
    except Error as e:
        import sys; print(f"[FATAL] Cannot connect to MySQL: {e}"); sys.exit(1)
    app = KVKFlyzz(); app.mainloop()