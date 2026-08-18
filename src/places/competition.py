import os

import requests
import pandas as pd

from dotenv import load_dotenv



# LOAD ENVIRONMENT VARIABLES


load_dotenv()                          #Here we load the environment variables from a .env file into the environment.

google_maps_key = os.getenv(
    "GOOGLE_MAPS_API_KEY"
)



SUPPORTED_BUSINESS_TYPES = {           # set of supported business types.
    "restaurant",
    "cafe",
    "bakery",
    "bar",
    "pub",

    "pizza_restaurant",
    "ramen_restaurant",
    "sushi_restaurant",
    "chinese_restaurant",
    "indian_restaurant",
    "north_indian_restaurant",
    "south_indian_restaurant",

    "thai_restaurant",
    "korean_restaurant",
    "mexican_restaurant",

    "hamburger_restaurant",
    "shawarma_restaurant",
    "taco_restaurant",

    "noodle_shop",
    "ice_cream_shop",

    "fast_food_restaurant"
}


def validate_business_type(             # this function ensures that the provided business type is a valid Google Places business type. It raises errors for invalid inputs and returns the cleaned business type if valid.
    business_type: str
) -> str:
    """
    Validate a Google Places business type.

    The function expects a Google Places type such as:

        cafe
        pizza_restaurant
        ramen_restaurant
        ice_cream_shop

    It does not try to interpret arbitrary user language.
    """

    if not isinstance(business_type,str):           #if the business type is not a string, raise a TypeError.
        raise TypeError(
            "business_type must be a string."
        )

    business_type = (business_type.strip().lower())       # cleans the business type by stripping whitespace and converting to lowercase.
    

    if not business_type:                               # if user provides an empty string, raise a ValueError.
        raise ValueError(
            "business_type cannot be empty."
        )

    if business_type not in (SUPPORTED_BUSINESS_TYPES):        # if the business type is not in the list of supported business types, raise a ValueError.
        raise ValueError(
            f"Unsupported Google Places "
            f"business type: "
            f"'{business_type}'"
        )

    return business_type
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def resolve_location_coordinates(                     # its purpose is to convert a human-readable location into latitude and longitude coordinates using the Google Places Text Search API. It raises errors for invalid inputs.
    location: str
) -> tuple[float, float]:
    """
    Resolve a human-readable location into
    latitude and longitude using Google Places Text Search.

    Example:
        "Brookfield, Bengaluru"
        "Indiranagar, Bengaluru"
        "Whitefield, Bengaluru"
    """

    if not google_maps_key:
        raise ValueError(
            "GOOGLE_MAPS_API_KEY not found in .env"
        )

    if not isinstance(location, str):
        raise TypeError(
            "location must be a string."
        )

    location = location.strip()

    if not location:
        raise ValueError(
            "location cannot be empty."
        )

    url = (                                     # code uses the Google Places Text Search API to resolve the location into coordinates.
        "https://places.googleapis.com/v1/"     # it is the base address for the Google Places API.
        "places:searchText"                     # it means that the API will perform a text-based search for places based on the provided location string.
    )

    headers = {                                # it tells google places api how to process request and what to return in response
        "Content-Type": "application/json",    # data is being sent in json format, and the client expects a JSON response from the API.

        "X-Goog-Api-Key": (
            google_maps_key
        ),

        "X-Goog-FieldMask": (                 # it tells the API which specific fields of information about the places should be included in the response.
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.location"
        )
    }

    payload = {                              # payload meaning= what are we asking to search for, and how many results we want.
        "textQuery": location,
        "maxResultCount": 1
    }

    response = requests.post(             # it sends a POST request to the Google Places API. The response from the API is stored in the response variable.
        url,
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        raise Exception(
            f"Places location resolution error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    places = data.get("places",[])
    

    if not places:
        raise ValueError(
            f"Could not resolve location "
            f"'{location}' using Google Places."
        )

    coordinates = places[0].get("location",{})     # it stores the coordinates of the first place returned by the API in the coordinates variable. If no location is found, it defaults to an empty dictionary.

    latitude = coordinates.get("latitude")         # if {} empty dictionary is returned, then latitude and longitude will be None. If the coordinates are found, it extracts the latitude and longitude values from the coordinates dictionary.
    longitude = coordinates.get("longitude")

    if latitude is None or longitude is None:
        raise ValueError(
            f"Google Places returned no coordinates "
            f"for location '{location}'."
        )

    return (
        float(latitude),
        float(longitude)
    )

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def get_nearby_competitors(     # based on the provided latitude, longitude, and business type, this function retrieves nearby competitors using the Google Places Nearby Search API. It raises errors for invalid inputs and returns a DataFrame containing competitor information.
    latitude,
    longitude,
    business_type,
    radius_km=3,
    max_results=20              #funxtion needs 5 inputs, latitude, longitude, business_type, radius_km, max_results.
):
    """
    Retrieve nearby competitors using Google Places
    Nearby Search API.

    This searches using a Google Places business type.
    """

    if not google_maps_key:
        raise ValueError(
            "GOOGLE_MAPS_API_KEY not found in .env"
        )

    # Validate Google Places type
    business_type = validate_business_type( business_type)

    url = (
        "https://places.googleapis.com/v1/"
        "places:searchNearby"                   # searchNearby endpoint of the Google Places API is used to find places near a specific location based on the provided latitude and longitude.
    )

    headers = {                                 # here we are defining the headers for the HTTP request to the Google Places API. These headers provide information about the request and specify how the API should respond.
        "Content-Type": "application/json",     # requests and responses will be in JSON format.

        "X-Goog-Api-Key": (
            google_maps_key
        ),

        "X-Goog-FieldMask": (                   # i want these specific fields in the response from the API.
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.rating,"
            "places.userRatingCount,"
            "places.priceLevel,"
            "places.types,"
            "places.location"
        )
    }

    payload = {
        "includedTypes": [business_type],    # this specifies the types of places to include in the search results. In this case, it includes only places that match the specified business type.
        "maxResultCount": max_results,

        "locationRestriction": {                 # this defines a circular area around the specified latitude and longitude within which the search will be restricted. The radius is specified in meters (radius_km * 1000).
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },

                "radius": radius_km * 1000
            }
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        raise Exception(
            f"Places API error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    data = response.json()              

    rows = []                            # empty list to store competitor information.

    for place in data.get("places",[]):  # loop through the list of places returned by the API. For each place, it extracts relevant information and appends it to the rows list as a dictionary.
        rows.append({
            "place_id": place.get("id"),
            "name": place.get("displayName",{}).get("text"),
            "address": place.get("formattedAddress"),
            "rating": place.get("rating"),
            "review_count": place.get("userRatingCount"),
            "price_level": place.get("priceLevel"),
            "types": place.get("types"),
            "latitude": place.get("location",{}).get("latitude"),
            "longitude": place.get("location",{}).get("longitude")
        })

    df = pd.DataFrame(rows)       # it converts the list of competitor information into a pandas DataFrame for easier manipulation and analysis.

    if df.empty:
        return df

    # Remove duplicate businesses
    df = (df.drop_duplicates(subset="place_id").reset_index(drop=True))        # drop duplicates based on the "place_id" column to ensure that each competitor is represented only once in the DataFrame. The index is reset after dropping duplicates.

    return df                  # returns the DataFrame containing information about nearby competitors based on the specified criteria.

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def search_competitors_by_text(     # based on the provided latitude, longitude, and search query, this function searches for businesses using the Google Places Text Search API. It raises errors for invalid inputs and returns a DataFrame containing business information.
    latitude,
    longitude,
    search_query,                   # function needs 5 inputs: latitude, longitude, search_query, radius_km, max_results. Search query can be natural language like "ramen restaurants", "momos shops", "vegan bakery", etc.
    radius_km=3,
    max_results=20
):
    """
    Search for businesses using Google's Text Search API.

    This searches using a natural-language text query.
    """

    if not google_maps_key:
        raise ValueError(
            "GOOGLE_MAPS_API_KEY not found in .env"
        )

    # Validate that search_query is a string
    if not isinstance(search_query, str):
        raise TypeError(
            "search_query must be a string."
        )

    search_query = search_query.strip()   # removes unnecessary spaces from the beginning and end of the search query.

    if not search_query:
        raise ValueError(
            "search_query cannot be empty."
        )

    url = (
        "https://places.googleapis.com/v1/"
        "places:searchText"             # searchText endpoint of the Google Places API is used to find places based on a text query. Unlike searchNearby, this allows natural-language searches such as "ramen restaurants" or "vegan bakery".
    )

    headers = {                         # here we are defining the headers for the HTTP request to the Google Places API. These headers provide information about the request and specify how the API should respond.
        "Content-Type": "application/json",     # requests and responses will be in JSON format.

        "X-Goog-Api-Key": (
            google_maps_key
        ),

        "X-Goog-FieldMask": (           # i want these specific fields in the response from the API.
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.rating,"
            "places.userRatingCount,"
            "places.priceLevel,"
            "places.types,"
            "places.location"
        )
    }

    payload = {
        "textQuery": search_query,      # this specifies the text that Google should search for. It can be a natural-language query such as "ramen restaurants" or "protein meal restaurants".

        "maxResultCount": max_results,  # this specifies the maximum number of places that Google should return.

        "locationBias": {               # this tells Google to prefer/search around the specified latitude and longitude. The radius is specified in meters (radius_km * 1000).
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },

                "radius": radius_km * 1000
            }
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        raise Exception(
            f"Places Text Search API error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    data = response.json()              # converts the JSON response received from Google into a Python dictionary so that we can access the returned places.

    rows = []                           # empty list to store information about each business returned by the API.

    for place in data.get("places",[]): # loop through the list of places returned by the API. For each place, it extracts relevant information and appends it to the rows list as a dictionary.
        rows.append({
            "place_id": place.get("id"),
            "name": place.get("displayName",{}).get("text"),
            "address": place.get("formattedAddress"),
            "rating": place.get("rating"),
            "review_count": place.get("userRatingCount"),
            "price_level": place.get("priceLevel"),
            "types": place.get("types"),
            "latitude": place.get("location",{}).get("latitude"),
            "longitude": place.get("location",{}).get("longitude")
        })

    df = pd.DataFrame(rows)             # converts the list of business information into a pandas DataFrame for easier manipulation and analysis.

    if df.empty:
        return df

    # Remove duplicate businesses
    df = (df.drop_duplicates(subset="place_id").reset_index(drop=True))   # drops duplicate businesses based on the "place_id" column so that each business is represented only once. The index is reset after removing duplicates.

    return df
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def filter_relevant_competitors(
    competitors,
    business_type
):
    """
    Filter Google Places results and keep only
    direct competitors.

    Direct competitors:
        Businesses whose Google Places types match
        the proposed business type.
    """

    # No competitors returned
    if competitors.empty:
        return competitors.copy()

    relevant_rows = []

    # Check every Google Places result
    for _, row in competitors.iterrows():

        place_types = row.get("types",[])

        # Ensure types is a list
        if not isinstance(place_types, list):
            place_types = []

        # Direct competitor check
        is_direct = ( business_type in place_types)

        if is_direct:

            # Copy row so original DataFrame
            # is not modified
            row = row.copy()

            # Mark as direct competitor
            row["competition_category"] = "direct"
            relevant_rows.append(row)

    # No direct competitors found return an empty DataFrame
    if not relevant_rows:
        return pd.DataFrame()

    
    return pd.DataFrame(relevant_rows).reset_index(drop=True)               # converts the filtered competitor list back into a DataFrame and resets the index.


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def summarize_competition(competitors):
    """
    Calculate deterministic competition metrics
    from competitor data.

    IMPORTANT:
    Thresholds used here are part of the project's
    analytical definition.

        High rating  = >= 4.5
        High reviews = >= 2000
    """

    if competitors.empty:

        return {
            "competitor_count_retrieved": 0,

            "avg_competitor_rating": 0,

            "median_competitor_rating": 0,

            "avg_competitor_reviews": 0,

            "median_competitor_reviews": 0,

            "high_rating_competitors": 0,

            "high_review_competitors": 0
        }

    
    # Remove missing values
    ratings = (competitors["rating" ].dropna())
    reviews = (competitors["review_count"].dropna())

    competitor_count = len(competitors) # it counts the total number of competitors in the DataFrame, regardless of whether they have ratings or reviews. This gives a complete picture of the competitive landscape, including businesses that may not have received any ratings or reviews yet.
    

   
    # Rating statistics

    avg_rating = (ratings.mean() if len(ratings)else 0)

    median_rating = (ratings.median() if len(ratings)else 0)

    
    # Review statistics
    
    avg_reviews = (reviews.mean() if len(reviews)else 0)

    median_reviews = (reviews.median() if len(reviews)else 0)


    # Competition thresholds

    high_rating_competitors = (ratings >= 4.5).sum() # Count of competitors with ratings >= 4.5

    high_review_competitors = (reviews >= 2000).sum() # Count of competitors with reviews >= 2000

   
    # Final summary
    return {
    "competitor_count_retrieved": int(competitor_count),
    "avg_competitor_rating": round(float(avg_rating), 2),
    "median_competitor_rating": round(float(median_rating), 2),
    "avg_competitor_reviews": round(float(avg_reviews), 2),
    "median_competitor_reviews": round(float(median_reviews), 2),
    "high_rating_competitors": int(high_rating_competitors),
    "high_review_competitors": int(high_review_competitors)
}

