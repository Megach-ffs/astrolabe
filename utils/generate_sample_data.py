"""
Sample Data Generator.

Generates two sample datasets with intentional data quality issues
for testing the Data Wrangler & Visualizer application.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta


def generate_ecommerce_orders(output_path: str, n_rows: int = 1500):
    """Generate an e-commerce orders dataset with data quality issues."""
    np.random.seed(42)

    products = [
        "Laptop", "Mouse", "Keyboard", "Monitor", "Headphones",
        "Webcam", "USB Hub", "SSD Drive", "RAM Module", "Graphics Card",
        "Tablet", "Smartwatch", "Speaker", "Charger", "Cable Pack",
        "Phone Case", "Screen Protector", "Stylus", "Docking Station",
        "Power Bank", "Router", "Ethernet Cable", "Microphone", "Desk Lamp",
        "Chair Mat", "Wrist Rest", "Mouse Pad", "Laptop Stand", "Fan",
        "Surge Protector", "Printer", "Scanner", "Projector", "VR Headset",
        "Drone", "Camera", "Tripod", "Memory Card", "External HDD",
        "Adapter", "Splitter", "Hub", "Switch", "NAS",
        "Server Rack", "UPS", "KVM Switch", "Label Maker", "Shredder",
    ]

    categories_clean = [
        "Electronics", "Accessories", "Storage", "Peripherals",
        "Networking", "Audio", "Office", "Gaming",
    ]

    # Create intentionally messy categories (mixed case, trailing spaces)
    categories_messy = (
        categories_clean
        + [c.upper() for c in categories_clean[:3]]
        + [c.lower() + "  " for c in categories_clean[2:5]]
        + [" " + c for c in categories_clean[5:7]]
    )

    cities = [
        "London", "Manchester", "Birmingham", "Leeds", "Glasgow",
        "Liverpool", "Edinburgh", "Bristol", "Cardiff", "Belfast",
        "Newcastle", "Sheffield", "Nottingham", "Southampton", "Leicester",
        "Brighton", "Oxford", "Cambridge", "York", "Bath",
        "Plymouth", "Exeter", "Norwich", "Aberdeen", "Dundee",
        "Swansea", "Coventry", "Derby", "Stoke", "Reading",
    ]

    # Generate base data
    data = {
        "order_id": range(1, n_rows + 1),
        "customer_id": [f"CUST-{np.random.randint(100, 500):04d}" for _ in range(n_rows)],
        "product_name": np.random.choice(products, n_rows),
        "category": np.random.choice(categories_messy, n_rows),
        "price": np.random.uniform(5, 2500, n_rows).round(2),
        "quantity": np.random.randint(1, 10, n_rows),
        "order_date": [
            (datetime(2024, 1, 1) + timedelta(days=int(np.random.randint(0, 730)))).strftime(
                np.random.choice(["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y"])
            )
            for _ in range(n_rows)
        ],
        "shipping_city": np.random.choice(cities, n_rows),
        "discount_pct": np.random.uniform(0, 30, n_rows).round(1),
        "rating": np.random.uniform(1, 5, n_rows).round(1),
    }

    df = pd.DataFrame(data)

    # --- Inject data quality issues ---

    # 1. Make price column "dirty" — add currency symbols and commas to some
    dirty_price_idx = np.random.choice(n_rows, size=int(n_rows * 0.15), replace=False)
    for idx in dirty_price_idx[:len(dirty_price_idx) // 2]:
        df.at[idx, "price"] = f"${df.at[idx, 'price']}"
    for idx in dirty_price_idx[len(dirty_price_idx) // 2:]:
        val = float(str(df.at[idx, "price"]).replace("$", ""))
        df.at[idx, "price"] = f"{val:,.2f}"

    # 2. Inject missing values (~8%)
    for col in ["discount_pct", "rating", "shipping_city", "category"]:
        null_idx = np.random.choice(n_rows, size=int(n_rows * 0.08), replace=False)
        df.loc[null_idx, col] = np.nan

    # 3. Add duplicate rows (~3%)
    dup_idx = np.random.choice(n_rows, size=int(n_rows * 0.03), replace=False)
    duplicates = df.iloc[dup_idx].copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    # 4. Add outlier discounts
    outlier_idx = np.random.choice(len(df), size=15, replace=False)
    df.loc[outlier_idx, "discount_pct"] = np.random.choice([95, 99, 100, -5, -10], 15)

    df.to_csv(output_path, index=False)
    print(f"Generated ecommerce_orders.csv: {len(df)} rows, {len(df.columns)} columns")
    return df


def generate_weather_stations(output_path: str, n_rows: int = 1200):
    """Generate a weather stations dataset with data quality issues."""
    np.random.seed(123)

    stations = [f"WS-{i:03d}" for i in range(1, 41)]
    station_names = [
        "Highland Peak", "Coastal Bay", "River Valley", "Mountain Top",
        "Forest Glen", "Lake Shore", "Urban Center", "Desert Oasis",
        "Prairie View", "Canyon Edge", "Island Point", "Marsh Landing",
        "Glacier View", "Volcano Base", "Tundra Station", "Reef Watch",
        "Plains One", "Hills Gate", "Delta South", "Cape Storm",
        "Summit Alpha", "Basin Floor", "Ridge Line", "Plateau North",
        "Falls View", "Dune Watch", "Cliff Side", "Bay Bridge",
        "Meadow Park", "Storm Point", "Pine Ridge", "Coral Cove",
        "Wind Farm", "Solar Field", "Rain Gauge", "Snow Peak",
        "Thunder Pass", "Lightning Rod", "Hail Stone", "Frost Bite",
    ]

    regions = ["North", "South", "East", "West", "Central", "Coastal"]
    statuses = ["Active", "Inactive", "Maintenance"]
    status_weights = [0.75, 0.15, 0.10]  # Maintenance is rare

    data = {
        "station_id": np.random.choice(stations, n_rows),
        "station_name": [station_names[int(s.split("-")[1]) - 1]
                         for s in np.random.choice(stations, n_rows)],
        "date": [
            (datetime(2024, 1, 1) + timedelta(days=int(d))).strftime("%Y-%m-%d")
            for d in sorted(np.random.randint(0, 365, n_rows))
        ],
        "temperature_c": np.random.normal(15, 10, n_rows).round(1),
        "humidity_pct": np.random.uniform(20, 100, n_rows).round(1),
        "wind_speed_kmh": np.random.exponential(15, n_rows).round(1),
        "precipitation_mm": np.random.exponential(5, n_rows).round(1),
        "region": np.random.choice(regions, n_rows),
        "status": np.random.choice(statuses, n_rows, p=status_weights),
    }

    df = pd.DataFrame(data)

    # --- Inject data quality issues ---

    # 1. Sentinel outliers (999 for temperature)
    outlier_idx = np.random.choice(n_rows, size=20, replace=False)
    df.loc[outlier_idx, "temperature_c"] = 999.0

    # 2. Missing values (~7%)
    for col in ["temperature_c", "humidity_pct", "precipitation_mm", "status"]:
        null_idx = np.random.choice(n_rows, size=int(n_rows * 0.07), replace=False)
        df.loc[null_idx, col] = np.nan

    # 3. Blank strings instead of NaN for status
    blank_idx = np.random.choice(n_rows, size=int(n_rows * 0.03), replace=False)
    df.loc[blank_idx, "status"] = ""

    # 4. Negative wind speeds (invalid)
    neg_idx = np.random.choice(n_rows, size=10, replace=False)
    df.loc[neg_idx, "wind_speed_kmh"] = -abs(df.loc[neg_idx, "wind_speed_kmh"])

    df.to_excel(output_path, index=False, engine="openpyxl")
    print(f"Generated weather_stations.xlsx: {len(df)} rows, {len(df.columns)} columns")
    return df


if __name__ == "__main__":
    # Determine output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    sample_dir = os.path.join(project_dir, "sample_data")
    os.makedirs(sample_dir, exist_ok=True)

    generate_ecommerce_orders(os.path.join(sample_dir, "ecommerce_orders.csv"))
    generate_weather_stations(os.path.join(sample_dir, "weather_stations.xlsx"))
    print(f"\nSample datasets saved to: {sample_dir}")
