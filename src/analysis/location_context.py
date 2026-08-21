import os
import pandas as pd

# PROJECT ROOT

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),"../.."))
DATA_PATH = os.path.join(BASE_DIR,"data","processed","zomato_train_engineered.csv")

# LOCATION NORMALIZATION

def normalize_location(location: str) -> str:
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



# LOCATION CONTEXT
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
    df["_location_normalized"] = (df["location"].astype(str).apply(normalize_location))
          
    
    # Normalize user location
    requested_location = (normalize_location(location))

    # Find location, filter the required rows
    location_data = df[
        df["_location_normalized"]== requested_location
        ]
  
    # Location not found
    if location_data.empty:

        return {
            "location": location,
            "found": False,
            "message": (f"No historical data found "f"for location: {location}")
        }


    # Retrieve first matching row
  
    row = location_data.iloc[0]

    # Return location context
  
    return {

        # Preserve the original user input
        "location": location,

        "found": True,

        "historical_restaurant_count": int(row["historical_restaurant_count"]),

        "location_median_cost": float(row["location_median_cost"]),

        "location_online_order_rate": float(row["location_online_order_rate"]),

        "location_book_table_rate": float(row["location_book_table_rate"]),

        "location_cuisine_diversity": int(row["location_cuisine_diversity"]),

        "location_business_type_diversity": int(row["location_business_type_diversity"])
    }