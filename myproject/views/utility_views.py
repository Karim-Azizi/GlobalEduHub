import requests
import time
import logging
from django.http import JsonResponse
from myproject.models import Country, City

# API URLs
RESTCOUNTRIES_URL = "https://restcountries.com/v3.1/all"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Logger setup
logger = logging.getLogger("myproject.utility_views")

# Default timeout and retry settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 60  # in seconds


### LOCATION DATA UTILITIES ###

def fetch_countries_from_api():
    """
    Fetch countries from RestCountries API and update the database.
    """
    try:
        logger.info("Fetching countries from RestCountries API...")
        response = requests.get(RESTCOUNTRIES_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        countries_data = response.json()

        for country_data in countries_data:
            process_country(country_data)
        logger.info("Countries updated successfully.")
    except requests.RequestException as e:
        logger.error(f"Error fetching countries: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during country fetch: {e}")

def fetch_cities_from_nominatim(country_name):
    """
    Fetch cities for a given country using the Nominatim API.
    """
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"country": country_name, "format": "json", "addressdetails": 1, "limit": 100},
            headers={"User-Agent": "myproject/1.0"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching cities for {country_name}: {e}")
        return []


def process_country(country_data):
    """
    Process individual country data and update/create the database records.
    """
    try:
        # Validate country code
        country_code = country_data.get("cca2", "").upper()
        if not country_code or len(country_code) != 2:
            logger.warning(f"Skipping country with invalid/missing code: {country_data.get('name', {}).get('common', 'Unknown')}")
            return

        # Extract and clean phone code
        root = country_data.get("idd", {}).get("root", "")
        suffixes = "".join(country_data.get("idd", {}).get("suffixes", [""]))
        phone_code = (root + suffixes).strip()

        # Trim long phone codes
        if len(phone_code) > 20:
            logger.warning(f"Trimming phone code for {country_data.get('name', {}).get('common')} to 20 characters.")
            phone_code = phone_code[:20]

        # Extract additional details
        name = country_data.get("name", {}).get("common", "Unknown")
        region = country_data.get("region", "")
        subregion = country_data.get("subregion", "")
        population = country_data.get("population", 0)
        flag_url = country_data.get("flags", {}).get("png", "")

        # Update or create country
        country_obj, created = Country.objects.update_or_create(
            code=country_code,
            defaults={
                "name": name,
                "phone_code": phone_code,
                "region": region,
                "subregion": subregion,
                "population": population,
                "flag_url": flag_url,
            },
        )
        if created:
            logger.info(f"Added country: {country_obj.name}")
        else:
            logger.info(f"Updated country: {country_obj.name}")

        # Fetch and save cities for the country
        fetch_and_save_cities(country_obj)

    except KeyError as key_err:
        logger.error(f"KeyError for country {country_data.get('name', {}).get('common', 'Unknown')}: {key_err}")
    except Exception as e:
        logger.error(f"Unexpected error while processing country: {e}")


def fetch_cities_with_retry(country_name):
    """
    Fetch cities with retry logic to handle rate limits and temporary errors.
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                NOMINATIM_URL,
                params={"country": country_name, "format": "json", "addressdetails": 1, "limit": 100},
                headers={"User-Agent": "myproject/1.0"},
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 429:  # Too Many Requests
                logger.warning("Rate limit reached. Retrying after delay...")
                time.sleep(RETRY_DELAY)
                continue
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            logger.warning(f"Request timed out for {country_name}. Retrying...")
            time.sleep(RETRY_DELAY)
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Error fetching cities for {country_name}: {e}. Retrying...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed after {MAX_RETRIES} attempts for {country_name}: {e}")
                return []
    return []


def fetch_and_save_cities(country_obj):
    """
    Fetch cities for a given country and save them to the database.
    """
    logger.info(f"Fetching cities for {country_obj.name}...")
    cities_data = fetch_cities_with_retry(country_obj.name)

    if not cities_data:
        logger.warning(f"No cities found for {country_obj.name}.")
        return

    try:
        for city_data in cities_data:
            city_name = city_data.get("display_name", "").split(",")[0]
            lat = city_data.get("lat", None)
            lon = city_data.get("lon", None)

            City.objects.update_or_create(
                name=city_name.strip(),
                country=country_obj,
                defaults={
                    "latitude": lat,
                    "longitude": lon,
                },
            )
            logger.info(f"Saved city: {city_name} in {country_obj.name}")
    except Exception as e:
        logger.error(f"Unexpected error while saving cities for {country_obj.name}: {e}")


def update_countries_and_cities(request):
    """
    Update countries and cities via API calls.
    """
    try:
        fetch_countries_from_api()
        return JsonResponse({"status": "success", "message": "Countries and cities updated successfully."}, status=200)
    except Exception as e:
        logger.error(f"Error updating countries and cities: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def get_countries(request):
    """
    Retrieve all countries from the database.
    """
    try:
        countries = Country.objects.values("id", "name", "phone_code").order_by("name")
        return JsonResponse(list(countries), safe=False, status=200)
    except Exception as e:
        logger.error(f"Error fetching countries: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def get_cities(request, country_id):
    """
    Retrieve cities for a given country from the database.
    """
    try:
        country = Country.objects.get(id=country_id)
        cities = City.objects.filter(country=country).values("id", "name").order_by("name")
        if not cities.exists():
            # Fetch cities dynamically if not found
            cities_data = fetch_cities_with_retry(country.name)
            for city_data in cities_data:
                city_name = city_data.get("display_name", "").split(",")[0]
                City.objects.get_or_create(name=city_name.strip(), country=country)
            cities = City.objects.filter(country=country).values("id", "name").order_by("name")
        return JsonResponse(list(cities), safe=False, status=200)
    except Country.DoesNotExist:
        return JsonResponse({"error": "Country not found."}, status=404)
    except Exception as e:
        logger.error(f"Error fetching cities: {e}")
        return JsonResponse({"error": str(e)}, status=500)


def fetch_states_from_nominatim(country_name):
    """
    Fetch states/provinces for a given country using OpenStreetMap (Nominatim API).
    """
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"country": country_name, "state": "*", "format": "json", "limit": 50},
            headers={"User-Agent": "myproject/1.0"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching states for {country_name}: {e}")
        return []


def get_phone_code(request, country_id):
    """
    Retrieve the phone code for a specific country.
    """
    try:
        country = Country.objects.get(id=country_id)
        return JsonResponse({"phone_code": country.phone_code}, status=200)
    except Country.DoesNotExist:
        return JsonResponse({"error": "Country not found."}, status=404)
    except Exception as e:
        logger.error(f"Error fetching phone code: {e}")
        return JsonResponse({"error": str(e)}, status=500)