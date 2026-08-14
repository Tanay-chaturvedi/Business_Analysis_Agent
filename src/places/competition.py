import os

import requests
import pandas as pd

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

google_maps_key = os.getenv(
    "GOOGLE_MAPS_API_KEY"
)


# ============================================================
# GOOGLE PLACES TYPE VALIDATION
# ============================================================

# Google Places types that we currently allow our
# application to send to Nearby Search.
#
# This is intentionally a validation layer, not a huge
# hard-coded natural-language mapping.

SUPPORTED_BUSINESS_TYPES = {
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


def validate_business_type(
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

    if not isinstance(
        business_type,
        str
    ):
        raise TypeError(
            "business_type must be a string."
        )

    business_type = (
        business_type
        .strip()
        .lower()
    )

    if not business_type:
        raise ValueError(
            "business_type cannot be empty."
        )

    if business_type not in (
        SUPPORTED_BUSINESS_TYPES
    ):
        raise ValueError(
            f"Unsupported Google Places "
            f"business type: "
            f"'{business_type}'"
        )

    return business_type


# ============================================================
# GOOGLE PLACES — NEARBY SEARCH
# ============================================================

def get_nearby_competitors(
    latitude,
    longitude,
    business_type,
    radius_km=3,
    max_results=20
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
    business_type = validate_business_type(
        business_type
    )

    url = (
        "https://places.googleapis.com/v1/"
        "places:searchNearby"
    )

    headers = {
        "Content-Type": "application/json",

        "X-Goog-Api-Key": (
            google_maps_key
        ),

        "X-Goog-FieldMask": (
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
        "includedTypes": [
            business_type
        ],

        "maxResultCount": max_results,

        "locationRestriction": {
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

    rows = []

    for place in data.get(
        "places",
        []
    ):

        rows.append({
            "place_id": place.get(
                "id"
            ),

            "name": place.get(
                "displayName",
                {}
            ).get(
                "text"
            ),

            "address": place.get(
                "formattedAddress"
            ),

            "rating": place.get(
                "rating"
            ),

            "review_count": place.get(
                "userRatingCount"
            ),

            "price_level": place.get(
                "priceLevel"
            ),

            "types": place.get(
                "types"
            ),

            "latitude": place.get(
                "location",
                {}
            ).get(
                "latitude"
            ),

            "longitude": place.get(
                "location",
                {}
            ).get(
                "longitude"
            )
        })

    df = pd.DataFrame(
        rows
    )

    if df.empty:
        return df

    # Remove duplicate businesses
    df = (
        df
        .drop_duplicates(
            subset="place_id"
        )
        .reset_index(
            drop=True
        )
    )

    return df


# ============================================================
# GOOGLE PLACES — TEXT SEARCH
# ============================================================

def search_competitors_by_text(
    latitude,
    longitude,
    search_query,
    radius_km=3,
    max_results=20
):
    """
    Search for businesses using Google's Text Search API.

    Useful for natural-language concepts such as:

        "ramen restaurants"
        "momos shops"
        "vegan bakery"
        "dessert parlour"
        "protein meal restaurants"

    IMPORTANT:
    Text Search results are broader candidates.
    They should not automatically be treated as direct
    competitors without relevance filtering.
    """

    if not google_maps_key:
        raise ValueError(
            "GOOGLE_MAPS_API_KEY not found in .env"
        )

    if not isinstance(
        search_query,
        str
    ):
        raise TypeError(
            "search_query must be a string."
        )

    search_query = (
        search_query
        .strip()
    )

    if not search_query:
        raise ValueError(
            "search_query cannot be empty."
        )

    url = (
        "https://places.googleapis.com/v1/"
        "places:searchText"
    )

    headers = {
        "Content-Type": "application/json",

        "X-Goog-Api-Key": (
            google_maps_key
        ),

        "X-Goog-FieldMask": (
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
        "textQuery": search_query,

        "maxResultCount": max_results,

        "locationBias": {
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

    data = response.json()

    rows = []

    for place in data.get(
        "places",
        []
    ):

        rows.append({
            "place_id": place.get(
                "id"
            ),

            "name": place.get(
                "displayName",
                {}
            ).get(
                "text"
            ),

            "address": place.get(
                "formattedAddress"
            ),

            "rating": place.get(
                "rating"
            ),

            "review_count": place.get(
                "userRatingCount"
            ),

            "price_level": place.get(
                "priceLevel"
            ),

            "types": place.get(
                "types"
            ),

            "latitude": place.get(
                "location",
                {}
            ).get(
                "latitude"
            ),

            "longitude": place.get(
                "location",
                {}
            ).get(
                "longitude"
            )
        })

    df = pd.DataFrame(
        rows
    )

    if df.empty:
        return df

    # Remove duplicate businesses
    df = (
        df
        .drop_duplicates(
            subset="place_id"
        )
        .reset_index(
            drop=True
        )
    )

    return df


# ============================================================
# COMPETITOR RELEVANCE FILTER
# ============================================================

def filter_relevant_competitors(
    competitors,
    business_type,
    include_indirect=True
):
    """
    Filter Google Places Text Search results into
    relevant direct and indirect competitors.

    Direct competitors:
        Businesses whose Google Places types match
        the proposed business type.

    Indirect competitors:
        Closely related business categories that compete
        for similar customer demand.

    This function is deterministic and does not use Gemini.
    """

    if competitors.empty:
        return competitors.copy()

    # --------------------------------------------------------
    # Related Google Places categories
    # --------------------------------------------------------

    related_types = {

        "ramen_restaurant": {
            "ramen_restaurant",
            "noodle_shop",
            "japanese_restaurant",
            "asian_restaurant",
            "chinese_noodle_restaurant"
        },

        "pizza_restaurant": {
            "pizza_restaurant",
            "italian_restaurant"
        },

        "ice_cream_shop": {
            "ice_cream_shop",
            "dessert_restaurant",
            "dessert_shop",
            "bakery"
        },

        "cafe": {
            "cafe",
            "coffee_shop",
            "dessert_restaurant",
            "bakery"
        },

        "bakery": {
            "bakery",
            "dessert_shop",
            "dessert_restaurant",
            "cafe"
        },

        "sushi_restaurant": {
            "sushi_restaurant",
            "japanese_restaurant",
            "asian_restaurant"
        },

        "chinese_restaurant": {
            "chinese_restaurant",
            "chinese_noodle_restaurant",
            "noodle_shop",
            "asian_restaurant"
        },

        "indian_restaurant": {
            "indian_restaurant",
            "north_indian_restaurant",
            "south_indian_restaurant"
        },

        "north_indian_restaurant": {
            "north_indian_restaurant",
            "indian_restaurant"
        },

        "south_indian_restaurant": {
            "south_indian_restaurant",
            "indian_restaurant"
        },

        "hamburger_restaurant": {
            "hamburger_restaurant",
            "fast_food_restaurant"
        },

        "fast_food_restaurant": {
            "fast_food_restaurant",
            "hamburger_restaurant",
            "sandwich_shop"
        }
    }

    relevant_types = related_types.get(
        business_type,
        {business_type}
    )

    # --------------------------------------------------------
    # Determine relevance
    # --------------------------------------------------------

    relevant_rows = []

    for _, row in competitors.iterrows():

        place_types = row.get(
            "types",
            []
        )

        if not isinstance(
            place_types,
            list
        ):
            place_types = []

        # Direct match
        is_direct = (
            business_type in place_types
        )

        # Related/indirect match
        is_indirect = (
            any(
                place_type in relevant_types
                for place_type in place_types
            )
        )

        if is_direct:

            row = row.copy()

            row[
                "competition_category"
            ] = "direct"

            relevant_rows.append(row)

        elif (
            include_indirect
            and is_indirect
        ):

            row = row.copy()

            row[
                "competition_category"
            ] = "indirect"

            relevant_rows.append(row)

    if not relevant_rows:
        return competitors.iloc[
            0:0
        ].copy()

    return pd.DataFrame(
        relevant_rows
    ).reset_index(
        drop=True
    )
# ============================================================
# COMPETITION SUMMARY
# ============================================================

def summarize_competition(
    competitors
):
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

    # --------------------------------------------------------
    # Remove missing values
    # --------------------------------------------------------

    ratings = (
        competitors[
            "rating"
        ]
        .dropna()
    )

    reviews = (
        competitors[
            "review_count"
        ]
        .dropna()
    )

    # --------------------------------------------------------
    # Basic counts
    # --------------------------------------------------------

    competitor_count = len(
        competitors
    )

    # --------------------------------------------------------
    # Rating statistics
    # --------------------------------------------------------

    avg_rating = (
        ratings.mean()
        if len(ratings)
        else 0
    )

    median_rating = (
        ratings.median()
        if len(ratings)
        else 0
    )

    # --------------------------------------------------------
    # Review statistics
    # --------------------------------------------------------

    avg_reviews = (
        reviews.mean()
        if len(reviews)
        else 0
    )

    median_reviews = (
        reviews.median()
        if len(reviews)
        else 0
    )

    # --------------------------------------------------------
    # Competition thresholds
    # --------------------------------------------------------

    high_rating_competitors = (
        ratings >= 4.5
    ).sum()

    high_review_competitors = (
        reviews >= 2000
    ).sum()

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    return {

        "competitor_count_retrieved": int(
            competitor_count
        ),

        "avg_competitor_rating": round(
            float(avg_rating),
            3
        ),

        "median_competitor_rating": round(
            float(median_rating),
            3
        ),

        "avg_competitor_reviews": round(
            float(avg_reviews),
            2
        ),

        "median_competitor_reviews": round(
            float(median_reviews),
            2
        ),

        "high_rating_competitors": int(
            high_rating_competitors
        ),

        "high_review_competitors": int(
            high_review_competitors
        )
    }