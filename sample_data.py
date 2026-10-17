"""Optional: add demo vehicles and services so you can try every menu option.

It only runs if NO data files exist yet, so it can never overwrite your real records.
Dates are calculated from today, so the maintenance reminders always make sense.
"""

from datetime import date, timedelta
from pathlib import Path

from models import create_vehicle
from rules import MaintenancePolicy
from service_center import ServiceCenter, SERVICES_FILE, VEHICLES_FILE
from storage import DataStore


def days_ago(days):
    return date.today() - timedelta(days=days)


def main():
    data_folder = Path(__file__).resolve().parent / "data"
    if (data_folder / VEHICLES_FILE).exists() or (data_folder / SERVICES_FILE).exists():
        print("Data files already exist - sample data was NOT added. Your records are safe.")
        return

    center = ServiceCenter(DataStore(data_folder), MaintenancePolicy())

    # (type, reg no, owner, model, year, odometer when first registered)
    vehicles = [
        ("car", "TS09AB1234", "Ravi Kumar", "Maruti Swift", 2019, 20000),
        ("bike", "TS10CD5678", "Anita Rao", "Honda Activa", 2021, 15000),
        ("bike", "AP28EF4321", "Suresh Reddy", "Bajaj Pulsar", 2020, 8000),
        ("car", "TS07GH9999", "Meena Iyer", "Hyundai i10", 2023, 8500),
    ]
    for vehicle_type, reg_no, owner, model, year, odometer in vehicles:
        center.register_vehicle(create_vehicle(vehicle_type, reg_no=reg_no, owner=owner,
                                               model=model, year=year, odometer=odometer))

    # (reg no, days ago, odometer, type, work, parts cost)
    services = [
        ("TS09AB1234", 400, 21000, "full", "Engine oil, filters, brake check", 2800),
        ("TS09AB1234", 200, 31500, "basic", "Oil change and washing", 1200),
        ("TS10CD5678", 30, 18000, "basic", "Oil change", 350),
        ("AP28EF4321", 120, 9000, "full", "Oil, chain set, air filter", 900),
    ]
    for reg_no, ago, odometer, service_type, work, parts in services:
        center.add_service(reg_no, days_ago(ago), odometer, service_type, work, parts)

    # Cars and bikes have been driven since their last service.
    center.get_vehicle("TS09AB1234").odometer = 42000
    center.get_vehicle("TS10CD5678").odometer = 18800
    center.get_vehicle("AP28EF4321").odometer = 11000
    center.save()
    print("Sample data added: 4 vehicles and 4 service records.")


if __name__ == "__main__":
    main()
