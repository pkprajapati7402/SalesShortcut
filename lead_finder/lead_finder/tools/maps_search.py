"""
Google Maps search tool implementation.
"""

import logging
from typing import Dict, Any, List, Optional
from google.adk.tools import FunctionTool
import googlemaps
from ..config import GOOGLE_MAPS_API_KEY
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleMapsClient:
    """Google Maps API client wrapper for business searches."""

    def __init__(self):
        self.client = None
        self._api_key_checked = False
        logger.info(f"GoogleMapsClient init - API Key from config: {bool(GOOGLE_MAPS_API_KEY)}")
        logger.info(f"GoogleMapsClient init - API Key length: {len(GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else 0}")
        try:
            self._initialize_client()
        except Exception as e:
            logger.error(f"Failed to initialize in __init__: {e}")
            self.client = None

    def _initialize_client(self):
        """Initialize the Google Maps client."""
        logger.info(f"Initializing Google Maps client. API Key available: {bool(GOOGLE_MAPS_API_KEY)}, Key length: {len(GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else 0}")
        
        if not GOOGLE_MAPS_API_KEY:
            logger.warning("Google Maps API key not found. Using mock data.")
            raise ValueError("Google Maps API key is required for Google Maps client initialization.")

        try:
            self.client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
            logger.info("Successfully initialized Google Maps client")
            # Test the client with a simple request
            self.client.geocode("San Francisco")
            logger.info("Google Maps client tested successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Maps client: {e}")
            logger.error(f"API Key (first 10 chars): {GOOGLE_MAPS_API_KEY[:10] if GOOGLE_MAPS_API_KEY else 'N/A'}")
            self.client = None

    def _ensure_client(self):
        """Ensure client is initialized, try again if not."""
        if not self.client and not self._api_key_checked:
            self._api_key_checked = True
            # Try to reinitialize in case environment wasn't ready before
            from ..config import GOOGLE_MAPS_API_KEY as FRESH_API_KEY
            if FRESH_API_KEY and FRESH_API_KEY != GOOGLE_MAPS_API_KEY:
                logger.info("Retrying Google Maps client initialization with fresh API key")
                self._initialize_client()

    def _get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get detailed information for a place."""
        if not self.client or not place_id:
            return {}

        try:
            result = self.client.place(place_id=place_id)
            return result.get('result', {})
        except Exception as e:
            logger.error(f"Error getting place details for {place_id}: {e}")
            return {}

    def _get_primary_category(self, types: List[str]) -> str:
        """Get the primary business category from place types."""
        if not types:
            return ""

        # Prioritize business-related types
        business_types = [
            "restaurant", "cafe", "bar", "store", "shop", "retail",
            "service", "business", "establishment"
        ]

        for type_ in types:
            if any(bt in type_.lower() for bt in business_types):
                return type_

        return types[0] if types else ""

    def _get_open_status(self, hours: Dict[str, Any]) -> bool:
        """Get the current open status of a business."""
        return hours.get('open_now', False) if hours else False

    def _get_mock_results(self, city: str, business_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate mock results for testing."""
        logger.warning(f"RETURNING MOCK DATA for {city}! Client status: {self.client}, API key checked: {self._api_key_checked}")
        mock_businesses = [
            {
                "place_id": f"mock_{city.lower()}_1",
                "name": f"Mock Business 1 - {city}",
                "address": f"123 Main St, {city}",
                "phone": "555-0123",
                "website": "",  # No website
                "rating": 4.5,
                "total_ratings": 100,
                "category": business_type or "General Business",
                "price_level": 2,
                "is_open": True,
                "location": {"lat": 40.7128, "lng": -74.0060}
            },
            {
                "place_id": f"mock_{city.lower()}_2",
                "name": f"Mock Business 2 - {city}",
                "address": f"456 Oak Ave, {city}",
                "phone": "555-0456",
                "website": "",  # No website
                "rating": 4.0,
                "total_ratings": 75,
                "category": business_type or "General Business",
                "price_level": 1,
                "is_open": True,
                "location": {"lat": 40.7589, "lng": -73.9851}
            }
        ]
        return mock_businesses

    def search_businesses(
        self, 
        city: str, 
        business_type: Optional[str] = None,
        radius: int = 50000,  # 50km radius (increased from 25km)
        min_rating: float = 0.0,
        max_results: int = 500,  # Increased from 200
        exclude_websites: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for businesses in a specified city.

        Args:
            city: The name of the city to search in
            business_type: Optional business type filter
            radius: Search radius in meters (default: 25km)
            min_rating: Minimum rating filter (default: 0.0)
            max_results: Maximum number of results (default: 200)
            exclude_websites: If True, only return businesses without websites

        Returns:
            List of business information dictionaries
        """
        # Ensure client is available
        self._ensure_client()

        if not self.client:
            logger.info("Using mock data for business search - Google Maps client not available")
            logger.info(f"Client status: {self.client}, API key checked: {self._api_key_checked}")
            return self._get_mock_results(city, business_type)

        try:
            # First, get the city's location
            geocode_result = self.client.geocode(city)
            if not geocode_result:
                logger.error(f"Could not find location for city: {city}")
                return self._get_mock_results(city, business_type)

            location = geocode_result[0]['geometry']['location']
            logger.info(f"Found location for {city}: {location}")

            # Define common business types to search for if no specific type is provided
            common_business_types = [
                "restaurant", "cafe", "bar", "store", "shop", "retail", "salon",
                "bakery", "grocery", "food", "service", "repair", "contractor",
                "doctor", "dentist", "health", "fitness", "gym", "yoga", "spa",
                "beauty", "hair", "nail", "barber", "massage", "therapy",
                "auto", "car", "mechanic", "dealer", "parts", "tire", "detail",
                "real estate", "property", "apartment", "home", "house", "rental",
                "insurance", "financial", "bank", "accounting", "tax", "legal",
                "attorney", "lawyer", "education", "school", "tutor", "daycare",
                "child care", "pet", "veterinary", "animal", "landscaping", "lawn",
                "cleaning", "maid", "janitorial", "plumber", "electrician", "hvac",
                "construction", "roofing", "painting", "flooring", "furniture",
                "clothing", "apparel", "jewelry", "accessory", "shoe", "tailor",
                "electronics", "computer", "phone", "repair", "photography", "art",
                "craft", "hobby", "toy", "game", "book", "music", "instrument",
                "church", "religious", "nonprofit", "charity", "community",
                "event", "venue", "catering", "party", "wedding", "funeral",
                "moving", "storage", "shipping", "delivery", "transportation"
            ]

            all_results = []
            processed_place_ids = set()  # To avoid duplicates

            # If business_type is provided, only search for that type
            search_types = [business_type] if business_type else common_business_types  # Use all business types

            for search_type in search_types:
                if len(all_results) >= max_results:
                    break

                # Build search query
                if search_type:
                    query = f"{search_type} in {city}"
                else:
                    query = f"businesses in {city}"

                logger.info(f"Searching for: {query}")

                # Try both places and places_nearby for more comprehensive results
                search_methods = [
                    # Text search
                    lambda: self.client.places(
                        query=query,
                        location=location,
                        radius=radius
                    ),
                    # Nearby search with type
                    lambda: self.client.places_nearby(
                        location=location,
                        radius=radius,
                        type=search_type if search_type and search_type in [
                            "accounting", "airport", "amusement_park", "aquarium", "art_gallery",
                            "atm", "bakery", "bank", "bar", "beauty_salon", "bicycle_store",
                            "book_store", "bowling_alley", "bus_station", "cafe", "campground",
                            "car_dealer", "car_rental", "car_repair", "car_wash", "casino",
                            "cemetery", "church", "city_hall", "clothing_store", "convenience_store",
                            "courthouse", "dentist", "department_store", "doctor", "drugstore",
                            "electrician", "electronics_store", "embassy", "fire_station", "florist",
                            "funeral_home", "furniture_store", "gas_station", "gym", "hair_care",
                            "hardware_store", "hindu_temple", "home_goods_store", "hospital", "insurance_agency",
                            "jewelry_store", "laundry", "lawyer", "library", "light_rail_station",
                            "liquor_store", "local_government_office", "locksmith", "lodging", "meal_delivery",
                            "meal_takeaway", "mosque", "movie_rental", "movie_theater", "moving_company",
                            "museum", "night_club", "painter", "park", "parking", "pet_store", "pharmacy",
                            "physiotherapist", "plumber", "police", "post_office", "primary_school",
                            "real_estate_agency", "restaurant", "roofing_contractor", "rv_park", "school",
                            "secondary_school", "shoe_store", "shopping_mall", "spa", "stadium", "storage",
                            "store", "subway_station", "supermarket", "synagogue", "taxi_stand", "tourist_attraction",
                            "train_station", "transit_station", "travel_agency", "university", "veterinary_care",
                            "zoo"
                        ] else None
                    )
                ]

                for search_method in search_methods:
                    try:
                        places_result = search_method()

                        results = places_result.get('results', [])
                        logger.info(f"Found {len(results)} initial results for {search_type}")

                        # Filter out duplicates
                        new_results = [r for r in results if r.get('place_id') not in processed_place_ids]

                        # Add place_ids to processed set
                        for r in new_results:
                            processed_place_ids.add(r.get('place_id'))

                        all_results.extend(new_results)

                        # Handle pagination to get more results
                        next_page_token = places_result.get('next_page_token')
                        while next_page_token and len(all_results) < max_results:
                            import time
                            # Wait a bit before requesting the next page (API requirement)
                            time.sleep(2)

                            # Get next page of results
                            if "places" in search_method.__name__:
                                next_page = self.client.places(
                                    query=query,
                                    location=location,
                                    radius=radius,
                                    page_token=next_page_token
                                )
                            else:
                                next_page = self.client.places_nearby(
                                    location=location,
                                    radius=radius,
                                    type=search_type if search_type and search_type in [
                                        "accounting", "airport", "amusement_park", "aquarium", "art_gallery",
                                        "atm", "bakery", "bank", "bar", "beauty_salon", "bicycle_store",
                                        "book_store", "bowling_alley", "bus_station", "cafe", "campground",
                                        "car_dealer", "car_rental", "car_repair", "car_wash", "casino",
                                        "cemetery", "church", "city_hall", "clothing_store", "convenience_store",
                                        "courthouse", "dentist", "department_store", "doctor", "drugstore",
                                        "electrician", "electronics_store", "embassy", "fire_station", "florist",
                                        "funeral_home", "furniture_store", "gas_station", "gym", "hair_care",
                                        "hardware_store", "hindu_temple", "home_goods_store", "hospital", "insurance_agency",
                                        "jewelry_store", "laundry", "lawyer", "library", "light_rail_station",
                                        "liquor_store", "local_government_office", "locksmith", "lodging", "meal_delivery",
                                        "meal_takeaway", "mosque", "movie_rental", "movie_theater", "moving_company",
                                        "museum", "night_club", "painter", "park", "parking", "pet_store", "pharmacy",
                                        "physiotherapist", "plumber", "police", "post_office", "primary_school",
                                        "real_estate_agency", "restaurant", "roofing_contractor", "rv_park", "school",
                                        "secondary_school", "shoe_store", "shopping_mall", "spa", "stadium", "storage",
                                        "store", "subway_station", "supermarket", "synagogue", "taxi_stand", "tourist_attraction",
                                        "train_station", "transit_station", "travel_agency", "university", "veterinary_care",
                                        "zoo"
                                    ] else None,
                                    page_token=next_page_token
                                )

                            # Add new results
                            new_page_results = next_page.get('results', [])

                            # Filter out duplicates
                            new_page_results = [r for r in new_page_results if r.get('place_id') not in processed_place_ids]

                            # Add place_ids to processed set
                            for r in new_page_results:
                                processed_place_ids.add(r.get('place_id'))

                            all_results.extend(new_page_results)
                            logger.info(f"Added {len(new_page_results)} more results from next page for {search_type}")

                            # Update token for next page (if any)
                            next_page_token = next_page.get('next_page_token')

                            # Break if we've reached max_results
                            if len(all_results) >= max_results:
                                break
                    except Exception as e:
                        logger.error(f"Error in search method for {search_type}: {e}")
                        continue

            logger.info(f"Total places found across all searches: {len(all_results)}")

            # Process results to get business details
            businesses = []
            processed_businesses = set()  # To track businesses we've already processed

            for place in all_results:
                if len(businesses) >= max_results:
                    break

                place_id = place.get('place_id', '')

                # Skip if we've already processed this business
                if place_id in processed_businesses:
                    continue

                processed_businesses.add(place_id)

                # Get detailed information
                place_details = self._get_place_details(place_id)

                # Skip if no details found
                if not place_details:
                    continue

                # Filter by rating if specified
                rating = place_details.get('rating', place.get('rating', 0))
                if rating < min_rating:
                    continue

                # Handle website filtering if exclude_websites is True
                website = place_details.get('website', '')

                # More sophisticated website filtering:
                # 1. If exclude_websites is False, include all businesses
                # 2. If exclude_websites is True:
                #    - Include businesses with no website field
                #    - Include businesses with empty website strings
                #    - Include businesses with potentially placeholder websites
                if exclude_websites:
                    # Check if website exists and appears to be a real website
                    if website and all([
                        # Basic checks for a functional website
                        len(website) > 5,  # Longer than 5 chars
                        "." in website,    # Has a domain extension
                        not website.startswith("http://localhost"),  # Not a localhost
                        not website.endswith("example.com"),  # Not an example domain
                        not "placeholder" in website.lower(),  # Not a placeholder
                        not "coming-soon" in website.lower(),  # Not a coming soon site
                        not "under-construction" in website.lower(),  # Not under construction
                    ]):
                        # This appears to be a real, functional website - skip if excluding websites
                        logger.debug(f"Skipping business with functional website: {place_details.get('name')}")
                        continue

                # Extract business information
                business = {
                    "place_id": place_id,
                    "name": place_details.get('name', place.get('name', '')),
                    "address": place_details.get('formatted_address', place.get('formatted_address', '')),
                    "phone": place_details.get('formatted_phone_number', ''),
                    "website": website,
                    "rating": rating,
                    "total_ratings": place_details.get('user_ratings_total', 0),
                    "category": self._get_primary_category(place_details.get('types', place.get('types', []))),
                    "price_level": place_details.get('price_level', 0),
                    "is_open": self._get_open_status(place_details.get('opening_hours', {})),
                    "location": {
                        "lat": place.get('geometry', {}).get('location', {}).get('lat'),
                        "lng": place.get('geometry', {}).get('location', {}).get('lng')
                    }
                }

                # Only add businesses with valid information
                if business["name"] and business["address"]:
                    businesses.append(business)
                    logger.debug(f"Added business: {business['name']}")

            logger.info(f"Found {len(businesses)} valid businesses in {city}")
            return businesses

        except Exception as e:
            logger.error(f"Error searching businesses in {city}: {e}")
            return self._get_mock_results(city, business_type)

# Global client instance - initialized lazily
_maps_client = None

def _get_maps_client():
    """Get or create the global maps client instance."""
    global _maps_client
    if _maps_client is None:
        logger.info("Creating new GoogleMapsClient instance...")
        _maps_client = GoogleMapsClient()
    return _maps_client

def google_maps_search(
    city: str, 
    business_type: Optional[str] = None,
    min_rating: float = 0.0,  # Changed to 0.0 to get all businesses
    max_results: int = 500,  # Increased to 500 to get more results
    exclude_websites: bool = True  # Add parameter to filter websites
) -> Dict[str, Any]:
    """
    Enhanced Google Maps search for businesses in a specified city.

    Args:
        city: The name of the city to search in
        business_type: Optional business type filter
        min_rating: Minimum rating filter (default: 0.0)
        max_results: Maximum number of results (default: 500)
        exclude_websites: If True, only return businesses without websites (default: True)

    Returns:
        A dictionary containing search results and metadata
    """
    try:
        # Get the client instance (lazy initialization)
        maps_client = _get_maps_client()

        # Search for businesses
        businesses = maps_client.search_businesses(
            city=city,
            business_type=business_type,
            min_rating=min_rating,
            max_results=max_results,
            exclude_websites=exclude_websites
        )

        # No need to filter again as it's already done in search_businesses

        return {
            "status": "success",
            "total_results": len(businesses),
            "results": businesses,
            "search_metadata": {
                "city": city,
                "business_type": business_type,
                "min_rating": min_rating,
                "max_results": max_results,
                "api_available": maps_client.client is not None,
                "exclude_websites": exclude_websites
            }
        }

    except Exception as e:
        logger.error(f"Error in google_maps_search: {e}")
        maps_client = _get_maps_client() if '_maps_client' in globals() and _maps_client else None
        return {
            "status": "error",
            "message": str(e),
            "total_results": 0,
            "results": [],
            "search_metadata": {
                "city": city,
                "business_type": business_type,
                "min_rating": min_rating,
                "max_results": max_results,
                "api_available": maps_client.client is not None if maps_client else False,
                "exclude_websites": exclude_websites
            }
        }

# Enhanced function tool with support for multiple search types
def google_maps_nearby_search(city: str, business_type: str = "restaurant") -> Dict[str, Any]:
    """Search for specific business types nearby."""
    return google_maps_search(city, business_type=business_type)

def google_maps_high_rated_search(city: str, min_rating: float = 4.0) -> Dict[str, Any]:
    """Search for highly-rated businesses."""
    return google_maps_search(city, min_rating=min_rating)

# Create function tools
google_maps_search_tool = FunctionTool(func=google_maps_search)
google_maps_nearby_search_tool = FunctionTool(func=google_maps_nearby_search)
google_maps_high_rated_search_tool = FunctionTool(func=google_maps_high_rated_search)
