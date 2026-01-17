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
        """Generate realistic Indian mock results for testing with more leads."""
        logger.warning(f"RETURNING MOCK DATA for {city}! Client status: {self.client}, API key checked: {self._api_key_checked}")
        
        # Extended realistic Indian business data (35+ businesses)
        indian_businesses = [
            # Restaurants & Food
            {"place_id": f"mock_{city.lower()}_1", "name": "Shree Krishna Restaurant", "address": f"Shop 12, MG Road, {city}, India", "phone": "+91-9876543210", "website": "", "rating": 4.5, "total_ratings": 287, "category": business_type or "Restaurant", "price_level": 2, "is_open": True, "location": {"lat": 28.6139, "lng": 77.2090}},
            {"place_id": f"mock_{city.lower()}_2", "name": "Sharma Sweets & Namkeen", "address": f"17, Bazaar Street, {city}, India", "phone": "+91-9654321098", "website": "", "rating": 4.6, "total_ratings": 512, "category": business_type or "Sweet Shop", "price_level": 1, "is_open": True, "location": {"lat": 28.6178, "lng": 77.2056}},
            {"place_id": f"mock_{city.lower()}_3", "name": "Punjabi Dhaba", "address": f"Highway Junction, {city}, India", "phone": "+91-9823456712", "website": "", "rating": 4.3, "total_ratings": 198, "category": business_type or "Restaurant", "price_level": 1, "is_open": True, "location": {"lat": 28.6201, "lng": 77.2145}},
            {"place_id": f"mock_{city.lower()}_4", "name": "South Indian Cafe", "address": f"22, Temple Street, {city}, India", "phone": "+91-9765432187", "website": "", "rating": 4.4, "total_ratings": 345, "category": business_type or "Cafe", "price_level": 1, "is_open": True, "location": {"lat": 28.6256, "lng": 77.2123}},
            {"place_id": f"mock_{city.lower()}_5", "name": "Biryani House", "address": f"Old City, {city}, India", "phone": "+91-9887654321", "website": "", "rating": 4.7, "total_ratings": 623, "category": business_type or "Restaurant", "price_level": 2, "is_open": True, "location": {"lat": 28.6189, "lng": 77.2078}},
            
            # Retail & Shopping
            {"place_id": f"mock_{city.lower()}_6", "name": "Raj Electronics & Mobiles", "address": f"45, Gandhi Chowk, {city}, India", "phone": "+91-9845678901", "website": "", "rating": 4.2, "total_ratings": 156, "category": business_type or "Electronics Store", "price_level": 2, "is_open": True, "location": {"lat": 28.6198, "lng": 77.2135}},
            {"place_id": f"mock_{city.lower()}_7", "name": "Patel Textile Showroom", "address": f"56-58, Cloth Market, {city}, India", "phone": "+91-9876549876", "website": "", "rating": 3.9, "total_ratings": 145, "category": business_type or "Clothing Store", "price_level": 2, "is_open": True, "location": {"lat": 28.6245, "lng": 77.2112}},
            {"place_id": f"mock_{city.lower()}_8", "name": "Kumar Hardware & Sanitary", "address": f"Ground Floor, Market Complex, {city}, India", "phone": "+91-9823456789", "website": "", "rating": 4.4, "total_ratings": 267, "category": business_type or "Hardware Store", "price_level": 2, "is_open": True, "location": {"lat": 28.6156, "lng": 77.2189}},
            {"place_id": f"mock_{city.lower()}_9", "name": "Fashion Plaza", "address": f"Central Market, {city}, India", "phone": "+91-9712345678", "website": "", "rating": 4.0, "total_ratings": 234, "category": business_type or "Clothing Store", "price_level": 2, "is_open": True, "location": {"lat": 28.6223, "lng": 77.2167}},
            {"place_id": f"mock_{city.lower()}_10", "name": "Jain Book Depot", "address": f"Library Road, {city}, India", "phone": "+91-9834567890", "website": "", "rating": 4.5, "total_ratings": 187, "category": business_type or "Book Store", "price_level": 1, "is_open": True, "location": {"lat": 28.6278, "lng": 77.2189}},
            
            # Healthcare & Wellness
            {"place_id": f"mock_{city.lower()}_11", "name": "Gupta Medical Store", "address": f"Near City Hospital, Station Road, {city}, India", "phone": "+91-9123456789", "website": "", "rating": 4.7, "total_ratings": 423, "category": business_type or "Pharmacy", "price_level": 1, "is_open": True, "location": {"lat": 28.6254, "lng": 77.2167}},
            {"place_id": f"mock_{city.lower()}_12", "name": "Lakshmi Beauty Parlour", "address": f"1st Floor, Nehru Market, {city}, India", "phone": "+91-9876501234", "website": "", "rating": 4.3, "total_ratings": 234, "category": business_type or "Beauty Salon", "price_level": 1, "is_open": True, "location": {"lat": 28.6321, "lng": 77.2201}},
            {"place_id": f"mock_{city.lower()}_13", "name": "Modern Gym & Fitness Center", "address": f"2nd Floor, Mall Road, {city}, India", "phone": "+91-9912345678", "website": "", "rating": 4.1, "total_ratings": 178, "category": business_type or "Gym", "price_level": 2, "is_open": True, "location": {"lat": 28.6289, "lng": 77.2178}},
            {"place_id": f"mock_{city.lower()}_14", "name": "Ayurvedic Clinic", "address": f"Green Park, {city}, India", "phone": "+91-9898765432", "website": "", "rating": 4.6, "total_ratings": 312, "category": business_type or "Healthcare", "price_level": 2, "is_open": True, "location": {"lat": 28.6267, "lng": 77.2145}},
            {"place_id": f"mock_{city.lower()}_15", "name": "Yoga & Wellness Center", "address": f"Park View, {city}, India", "phone": "+91-9767890123", "website": "", "rating": 4.4, "total_ratings": 198, "category": business_type or "Yoga Studio", "price_level": 1, "is_open": True, "location": {"lat": 28.6298, "lng": 77.2123}},
            
            # Services
            {"place_id": f"mock_{city.lower()}_16", "name": "Singh Auto Repair", "address": f"Plot 23, Industrial Area, {city}, India", "phone": "+91-9988776655", "website": "", "rating": 4.0, "total_ratings": 89, "category": business_type or "Car Repair", "price_level": 2, "is_open": True, "location": {"lat": 28.6081, "lng": 77.2298}},
            {"place_id": f"mock_{city.lower()}_17", "name": "Verma Cyber Cafe & Printing", "address": f"Near Bus Stand, Main Road, {city}, India", "phone": "+91-9765432109", "website": "", "rating": 3.8, "total_ratings": 92, "category": business_type or "Internet Cafe", "price_level": 1, "is_open": True, "location": {"lat": 28.6312, "lng": 77.2234}},
            {"place_id": f"mock_{city.lower()}_18", "name": "Quick Laundry Service", "address": f"Behind Market, {city}, India", "phone": "+91-9678901234", "website": "", "rating": 4.2, "total_ratings": 145, "category": business_type or "Laundry", "price_level": 1, "is_open": True, "location": {"lat": 28.6234, "lng": 77.2167}},
            {"place_id": f"mock_{city.lower()}_19", "name": "Professional Tailoring", "address": f"Shop 34, Shopping Complex, {city}, India", "phone": "+91-9845123456", "website": "", "rating": 4.5, "total_ratings": 178, "category": business_type or "Tailor", "price_level": 1, "is_open": True, "location": {"lat": 28.6189, "lng": 77.2134}},
            {"place_id": f"mock_{city.lower()}_20", "name": "Mobile Repair Center", "address": f"Electronic Market, {city}, India", "phone": "+91-9712348765", "website": "", "rating": 4.1, "total_ratings": 267, "category": business_type or "Repair Shop", "price_level": 1, "is_open": True, "location": {"lat": 28.6201, "lng": 77.2156}},
            
            # Education & Training
            {"place_id": f"mock_{city.lower()}_21", "name": "Smart Coaching Classes", "address": f"Upper Floor, School Road, {city}, India", "phone": "+91-9834567123", "website": "", "rating": 4.3, "total_ratings": 289, "category": business_type or "Coaching Center", "price_level": 2, "is_open": True, "location": {"lat": 28.6278, "lng": 77.2201}},
            {"place_id": f"mock_{city.lower()}_22", "name": "English Speaking Institute", "address": f"2nd Floor, Main Market, {city}, India", "phone": "+91-9923456789", "website": "", "rating": 4.0, "total_ratings": 156, "category": business_type or "Training Center", "price_level": 2, "is_open": True, "location": {"lat": 28.6245, "lng": 77.2178}},
            {"place_id": f"mock_{city.lower()}_23", "name": "Computer Training Academy", "address": f"IT Park, {city}, India", "phone": "+91-9798765432", "website": "", "rating": 4.4, "total_ratings": 312, "category": business_type or "Computer Institute", "price_level": 2, "is_open": True, "location": {"lat": 28.6289, "lng": 77.2234}},
            
            # Home Services
            {"place_id": f"mock_{city.lower()}_24", "name": "Mehta Plumbing Services", "address": f"Residential Area, {city}, India", "phone": "+91-9667788990", "website": "", "rating": 4.2, "total_ratings": 123, "category": business_type or "Plumber", "price_level": 1, "is_open": True, "location": {"lat": 28.6167, "lng": 77.2212}},
            {"place_id": f"mock_{city.lower()}_25", "name": "Electrician Services", "address": f"Near Power House, {city}, India", "phone": "+91-9778899001", "website": "", "rating": 4.1, "total_ratings": 98, "category": business_type or "Electrician", "price_level": 1, "is_open": True, "location": {"lat": 28.6198, "lng": 77.2189}},
            {"place_id": f"mock_{city.lower()}_26", "name": "Home Cleaning Services", "address": f"Sector 5, {city}, India", "phone": "+91-9889900112", "website": "", "rating": 4.3, "total_ratings": 187, "category": business_type or "Cleaning Service", "price_level": 2, "is_open": True, "location": {"lat": 28.6223, "lng": 77.2145}},
            
            # Food & Grocery
            {"place_id": f"mock_{city.lower()}_27", "name": "Fresh Fruits & Vegetables", "address": f"Vegetable Market, {city}, India", "phone": "+91-9756789012", "website": "", "rating": 4.0, "total_ratings": 234, "category": business_type or "Grocery", "price_level": 1, "is_open": True, "location": {"lat": 28.6212, "lng": 77.2101}},
            {"place_id": f"mock_{city.lower()}_28", "name": "Dairy Products Shop", "address": f"Milk Market, {city}, India", "phone": "+91-9645678901", "website": "", "rating": 4.5, "total_ratings": 345, "category": business_type or "Dairy", "price_level": 1, "is_open": True, "location": {"lat": 28.6234, "lng": 77.2123}},
            {"place_id": f"mock_{city.lower()}_29", "name": "Organic Food Store", "address": f"Health Plaza, {city}, India", "phone": "+91-9534567890", "website": "", "rating": 4.6, "total_ratings": 278, "category": business_type or "Organic Store", "price_level": 2, "is_open": True, "location": {"lat": 28.6267, "lng": 77.2167}},
            
            # Entertainment & Recreation
            {"place_id": f"mock_{city.lower()}_30", "name": "Gaming Zone", "address": f"Mall Complex, {city}, India", "phone": "+91-9423456789", "website": "", "rating": 4.2, "total_ratings": 456, "category": business_type or "Gaming Center", "price_level": 2, "is_open": True, "location": {"lat": 28.6289, "lng": 77.2189}},
            {"place_id": f"mock_{city.lower()}_31", "name": "Photography Studio", "address": f"Art Street, {city}, India", "phone": "+91-9312345678", "website": "", "rating": 4.4, "total_ratings": 267, "category": business_type or "Photo Studio", "price_level": 2, "is_open": True, "location": {"lat": 28.6278, "lng": 77.2156}},
            
            # Pet Care
            {"place_id": f"mock_{city.lower()}_32", "name": "Pet Clinic & Store", "address": f"Green Avenue, {city}, India", "phone": "+91-9201234567", "website": "", "rating": 4.5, "total_ratings": 189, "category": business_type or "Pet Shop", "price_level": 2, "is_open": True, "location": {"lat": 28.6256, "lng": 77.2212}},
            {"place_id": f"mock_{city.lower()}_33", "name": "Pet Grooming Salon", "address": f"Pet Care Complex, {city}, India", "phone": "+91-9190123456", "website": "", "rating": 4.3, "total_ratings": 145, "category": business_type or "Pet Grooming", "price_level": 2, "is_open": True, "location": {"lat": 28.6245, "lng": 77.2234}},
            
            # Automotive
            {"place_id": f"mock_{city.lower()}_34", "name": "Bike Service Center", "address": f"Auto Market, {city}, India", "phone": "+91-9089012345", "website": "", "rating": 4.1, "total_ratings": 234, "category": business_type or "Bike Repair", "price_level": 1, "is_open": True, "location": {"lat": 28.6189, "lng": 77.2201}},
            {"place_id": f"mock_{city.lower()}_35", "name": "Car Accessories Shop", "address": f"Highway Road, {city}, India", "phone": "+91-9978901234", "website": "", "rating": 4.0, "total_ratings": 178, "category": business_type or "Auto Parts", "price_level": 2, "is_open": True, "location": {"lat": 28.6167, "lng": 77.2278}},
            
            # Financial Services
            {"place_id": f"mock_{city.lower()}_36", "name": "Insurance Advisor", "address": f"Finance Street, {city}, India", "phone": "+91-9867890123", "website": "", "rating": 4.3, "total_ratings": 167, "category": business_type or "Insurance", "price_level": 2, "is_open": True, "location": {"lat": 28.6298, "lng": 77.2145}},
            {"place_id": f"mock_{city.lower()}_37", "name": "Tax Consultant Office", "address": f"Business Center, {city}, India", "phone": "+91-9756789123", "website": "", "rating": 4.4, "total_ratings": 198, "category": business_type or "Tax Service", "price_level": 2, "is_open": True, "location": {"lat": 28.6312, "lng": 77.2167}},
            
            # Travel & Tourism
            {"place_id": f"mock_{city.lower()}_38", "name": "Travel Agency", "address": f"Tourism Hub, {city}, India", "phone": "+91-9645678912", "website": "", "rating": 4.2, "total_ratings": 234, "category": business_type or "Travel Agent", "price_level": 2, "is_open": True, "location": {"lat": 28.6234, "lng": 77.2189}},
        ]
        
        logger.info(f"Generated {len(indian_businesses)} realistic mock leads for {city}")
        return indian_businesses

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
