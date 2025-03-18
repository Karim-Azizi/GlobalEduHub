from django.core.management.base import BaseCommand
from myproject.models import Country, City, PhoneCode

class Command(BaseCommand):
    help = "Populates the database with countries, cities, and phone codes"

    def handle(self, *args, **kwargs):
        countries = [
            {"code": "US", "name": "United States", "phone_code": "1", "cities": ["New York", "Los Angeles", "Chicago"]},
            {"code": "CA", "name": "Canada", "phone_code": "1", "cities": ["Toronto", "Vancouver", "Montreal"]},
            {"code": "GB", "name": "United Kingdom", "phone_code": "44", "cities": ["London", "Manchester", "Birmingham"]},
            {"code": "FR", "name": "France", "phone_code": "33", "cities": ["Paris", "Lyon", "Marseille"]},
            {"code": "DE", "name": "Germany", "phone_code": "49", "cities": ["Berlin", "Munich", "Frankfurt"]},
            {"code": "IN", "name": "India", "phone_code": "91", "cities": ["Mumbai", "Delhi", "Bangalore"]},
        ]

        for country_data in countries:
            country, created = Country.objects.get_or_create(code=country_data["code"], name=country_data["name"])
            PhoneCode.objects.get_or_create(country=country, code=country_data["phone_code"])

            for city_name in country_data["cities"]:
                City.objects.get_or_create(name=city_name, country=country)

        self.stdout.write(self.style.SUCCESS("Database populated successfully!"))