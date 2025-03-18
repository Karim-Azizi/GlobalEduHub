import requests
import time
from django.core.management.base import BaseCommand
from myproject.models import Country, City

# RestCountries API URL
RESTCOUNTRIES_URL = "https://restcountries.com/v3.1/all"
# OpenStreetMap (Nominatim API) for cities
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Default timeout and retry settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff multiplier


def fetch_cities_with_retry(country_name, retries=MAX_RETRIES, delay=60):
    """Fetch cities with retry logic and exponential backoff to handle rate limits and errors."""
    for attempt in range(retries):
        try:
            response = requests.get(
                NOMINATIM_URL,
                params={"country": country_name, "format": "json", "addressdetails": 1},
                headers={"User-Agent": "YourAppName/1.0"},
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 429:  # Too Many Requests
                print(f"Rate limit reached. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= RETRY_BACKOFF_FACTOR  # Exponential backoff
                continue
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"Timeout fetching cities for {country_name}. Retrying...")
            time.sleep(delay)
        except requests.RequestException as e:
            if attempt < retries - 1:
                print(f"Error fetching cities for {country_name}: {e}. Retrying...")
                time.sleep(delay)
                delay *= RETRY_BACKOFF_FACTOR
            else:
                print(f"Failed after {retries} attempts: {e}")
                return []
    return []


class Command(BaseCommand):
    help = "Fetch and update country and city data using RestCountries API and OpenStreetMap (Nominatim API)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Fetching countries from RestCountries API...")

        try:
            # Fetch data from RestCountries API with timeout
            response = requests.get(RESTCOUNTRIES_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            countries = response.json()

            for country in countries:
                self.process_country(country)

        except requests.Timeout:
            self.stderr.write("Request to RestCountries API timed out.")
        except requests.RequestException as req_err:
            self.stderr.write(f"Failed to fetch countries: {req_err}")
        except Exception as e:
            self.stderr.write(f"Unexpected error: {e}")

        self.stdout.write(self.style.SUCCESS("Countries and cities update process completed."))

    def process_country(self, country):
        """Process a single country: validate and update/create country record, and fetch cities."""
        try:
            # Validate ISO Alpha-2 country code
            country_code = country.get("cca2", "").upper()
            if not country_code or len(country_code) != 2:
                self.stderr.write(f"Skipping country with invalid or missing code: {country.get('name', {}).get('common', 'Unknown')}")
                return

            # Validate and clean phone code
            root = country.get("idd", {}).get("root", "")
            suffixes = "".join(country.get("idd", {}).get("suffixes", [""]))
            phone_code = (root + suffixes).strip()
            if len(phone_code) > 20:
                self.stdout.write(f"Warning: Trimming phone code for {country.get('name', {}).get('common')} to 20 characters.")
                phone_code = phone_code[:20]

            # Extract additional country details
            name = country.get("name", {}).get("common", "Unknown")
            region = country.get("region", "")
            subregion = country.get("subregion", "")
            population = country.get("population", 0)
            flag_url = country.get("flags", {}).get("png", "")

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
                self.stdout.write(f"Added country: {country_obj.name}")
            else:
                self.stdout.write(f"Updated country: {country_obj.name}")

            # Fetch cities for the country
            self.fetch_and_save_cities(country_obj)

        except KeyError as key_err:
            self.stderr.write(f"KeyError for country {country.get('name', {}).get('common', 'Unknown')}: {key_err}")
        except Exception as e:
            self.stderr.write(f"Unexpected error while processing country {country.get('name', {}).get('common', 'Unknown')}: {e}")

    def fetch_and_save_cities(self, country_obj):
        """Fetch cities for a given country using OpenStreetMap (Nominatim API) and save them to the database."""
        self.stdout.write(f"Fetching cities for {country_obj.name}...")

        cities_data = fetch_cities_with_retry(country_obj.name)

        if not cities_data:
            self.stderr.write(f"No cities found for {country_obj.name}.")
            return

        try:
            for city_data in cities_data:
                # Extract city details
                name = city_data.get("display_name", "").split(",")[0]
                lat = city_data.get("lat", None)
                lon = city_data.get("lon", None)

                # Save city data to the database
                City.objects.update_or_create(
                    name=name.strip(),
                    country=country_obj,
                    defaults={
                        "latitude": lat,
                        "longitude": lon,
                        "population": None,  # Nominatim API doesn't provide population data
                    },
                )
                self.stdout.write(f"Saved city: {name} in {country_obj.name}")

        except Exception as e:
            self.stderr.write(f"Unexpected error while saving cities for {country_obj.name}: {e}")