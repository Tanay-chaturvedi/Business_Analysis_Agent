import os
import pandas as pd

# PROJECT ROOT

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
DATA_PATH = os.path.join(BASE_DIR,"data","processed","zomato_train_engineered.csv")

# LOCATION NORMALIZATION

def normalize_location(location: str) -> str:      # It is called inside get_location_context()
    """
    Normalize user-provided location names.

    Examples:

        Whitefield
        Whitefield, Bengaluru
        Whitefield, Bangalore
        Whitefield Bengaluru

    become:

        whitefield
    """
    location = (str(location).strip().lower())
    
    suffixes = [
        ", bengaluru",
        ", bangalore",
        ", karnataka",
        " bengaluru",
        " bangalore",
        " karnataka"
    ]

    for suffix in suffixes:

        if location.endswith(suffix):
            location = location[:-len(suffix)].strip()
    return location     # returns location as string



def get_location_context(location: str) -> dict:
    """
    Retrieve historical location-level business context
    required by the ML prediction model.

    Returns:
        historical_restaurant_count
        location_median_cost
        location_online_order_rate
        location_book_table_rate
        location_cuisine_diversity
        location_business_type_diversity
    """
    df = pd.read_csv(DATA_PATH)

    # Normalize dataset locations and store in new column "_location_normalized"
    df["_location_normalized"] = df["location"].astype(str).apply(normalize_location)
    
    # Normalize user location
    requested_location = normalize_location(location)

    # Find location, filter the required rows
    location_data = df[df["_location_normalized"] == requested_location]

    # Location not found
    if location_data.empty:
        return {
            "location": location,
            "found": False,
            "message": f"No historical data found for location: {location}"
        }

    total_count = len(location_data)

    # Calculate actual rates from categorical/boolean restaurant records
    online_order_yes_count = len(location_data[location_data["online_order"].astype(str).str.lower().isin(["yes", "1", "true"])])
    book_table_yes_count = len(location_data[location_data["book_table"].astype(str).str.lower().isin(["yes", "1", "true"])])

    online_order_rate = float(online_order_yes_count / total_count) if total_count > 0 else 0.0
    book_table_rate = float(book_table_yes_count / total_count) if total_count > 0 else 0.0

    # Retrieve first matching row for fallback metadata
    row = location_data.iloc[0]

    # Top cuisines & types if present
    top_cuisines = list(location_data["primary_cuisine"].dropna().value_counts().head(5).index) if "primary_cuisine" in location_data.columns else []
    top_rest_types = list(location_data["primary_rest_type"].dropna().value_counts().head(5).index) if "primary_rest_type" in location_data.columns else []

    median_cost = float(location_data["approx_costfor_two_people"].median()) if "approx_costfor_two_people" in location_data.columns else float(row["location_median_cost"])

    # Debug log for verification
    print(f"[LocationContext] '{location}' -> matched {total_count} records. online_order_rate={online_order_rate:.4f}, book_table_rate={book_table_rate:.4f}")

    return {
        "location": location,
        "found": True,
        "historical_restaurant_count": total_count,
        "restaurant_count": total_count,
        "location_median_cost": median_cost,
        "online_order_yes_count": online_order_yes_count,
        "book_table_yes_count": book_table_yes_count,
        "location_online_order_rate": online_order_rate,
        "location_book_table_rate": book_table_rate,
        "online_order_rate": online_order_rate,
        "book_table_rate": book_table_rate,
        "historical_online_order_rate": online_order_rate,
        "historical_table_booking_rate": book_table_rate,
        "location_cuisine_diversity": int(row.get("location_cuisine_diversity", len(top_cuisines))),
        "location_business_type_diversity": int(row.get("location_business_type_diversity", len(top_rest_types))),
        "top_cuisines": top_cuisines,
        "top_rest_types": top_rest_types
    }