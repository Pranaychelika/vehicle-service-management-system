"""Vehicle Service & Maintenance Management System - terminal menu. Run this file."""

from datetime import date
from pathlib import Path
from export_data import export_to_excel

from models import (create_vehicle, validate_cost, validate_date, validate_odometer,
                    validate_reg_no, validate_service_type, validate_text,
                    validate_vehicle_type, validate_year)
from rules import CURRENCY, SERVICE_TYPES, MaintenancePolicy
from service_center import ServiceCenter, ServiceCenterError
from storage import DataStore


# ---------- input helpers ----------
def ask(prompt, validator, default=None):
    """Ask until the validator accepts the answer. Blank input gives `default` (if set)."""
    while True:
        text = input(prompt).strip()
        if text == "" and default is not None:
            return default
        try:
            return validator(text)
        except ValueError as error:
            print(f"  Invalid input: {error}")


def ask_optional(prompt, validator):
    """Like ask(), but blank input returns None, meaning 'keep the current value'."""
    while True:
        text = input(prompt).strip()
        if text == "":
            return None
        try:
            return validator(text)
        except ValueError as error:
            print(f"  Invalid input: {error}")


def validate_yes_no(text):
    answer = text.lower()
    if answer in ("y", "yes"):
        return True
    if answer in ("n", "no"):
        return False
    raise ValueError("Please answer y or n.")


def money(amount):
    return f"{CURRENCY} {amount:,.2f}"


def save_data(center):
    try:
        center.save()
    except OSError as error:
        print(f"WARNING: could not save data ({error}). Your changes are NOT saved yet.")


# ---------- display helpers ----------
def last_service_text(vehicle):
    if vehicle.last_service_date is None:
        return "Never"
    return f"{vehicle.last_service_date} ({vehicle.last_service_odometer} km)"


def print_vehicle_table(vehicles):
    print(f"{'Reg No':<13}{'Type':<6}{'Model':<18}{'Year':<6}{'Owner':<16}"
          f"{'Odometer':>9}  Last service")
    print("-" * 85)
    for v in vehicles:
        print(f"{v.reg_no:<13}{v.get_type():<6}{v.model[:17]:<18}{v.year:<6}{v.owner[:15]:<16}"
              f"{v.odometer:>9}  {last_service_text(v)}")


def print_history_table(records):
    print(f"{'ID':<4}{'Date':<12}{'Odometer':>9}  {'Type':<8}{'Work performed':<30}"
          f"{'Parts':>10}{'Labour':>10}{'Total':>11}")
    print("-" * 95)
    for r in records:
        print(f"{r.service_id:<4}{str(r.service_date):<12}{r.odometer:>9}  "
              f"{r.service_type:<8}{r.work_done[:29]:<30}"
              f"{r.parts_cost:>10,.2f}{r.labour_cost:>10,.2f}{r.total_cost:>11,.2f}")


def ask_vehicle(center, prompt="Registration number: "):
    return center.get_vehicle(ask(prompt, validate_reg_no))


# ---------- menu actions (one function per menu option) ----------
def register_vehicle(center):
    print("\n--- Register a new vehicle ---")
    reg_no = ask("Registration number: ", validate_reg_no)
    center.check_reg_no_available(reg_no)
    vehicle_type = ask("Vehicle type (car/bike): ", validate_vehicle_type)
    owner = ask("Owner name: ", validate_text)
    model = ask("Model: ", validate_text)
    year = ask("Manufacturing year: ", validate_year)
    odometer = ask("Current odometer reading (km): ", validate_odometer)
    last_date = last_odometer = None
    if ask("Has it been serviced before? (y/n): ", validate_yes_no):
        last_date = ask("Date of last service (YYYY-MM-DD): ", validate_date)
        last_odometer = ask("Odometer at last service (km): ", validate_odometer)

    vehicle = create_vehicle(vehicle_type, reg_no=reg_no, owner=owner, model=model, year=year,
                             odometer=odometer, last_service_date=last_date,
                             last_service_odometer=last_odometer)
    center.register_vehicle(vehicle)
    save_data(center)
    print(f"\nRegistered {vehicle}.")


def show_all_vehicles(center):
    vehicles = center.all_vehicles()
    if not vehicles:
        print("\nNo vehicles registered yet.")
        return
    print(f"\n--- All registered vehicles ({len(vehicles)}) ---")
    print_vehicle_table(vehicles)


def search_vehicle(center):
    vehicle = ask_vehicle(center, "Registration number to search: ")
    print(f"\nRegistration no : {vehicle.reg_no}")
    print(f"Type            : {vehicle.get_type().title()}")
    print(f"Model / Year    : {vehicle.model} / {vehicle.year}")
    print(f"Owner           : {vehicle.owner}")
    print(f"Odometer        : {vehicle.odometer} km")
    print(f"Last service    : {last_service_text(vehicle)}")
    print(f"Services done   : {len(center.get_history(vehicle.reg_no))}")


def update_vehicle(center):
    vehicle = ask_vehicle(center, "Registration number of the vehicle to update: ")
    print("Press Enter to keep the current value. (Vehicle type cannot be changed.)")
    new_reg_no = ask_optional(f"Registration number [{vehicle.reg_no}]: ", validate_reg_no)
    owner = ask_optional(f"Owner name [{vehicle.owner}]: ", validate_text)
    model = ask_optional(f"Model [{vehicle.model}]: ", validate_text)
    year = ask_optional(f"Manufacturing year [{vehicle.year}]: ", validate_year)
    odometer = ask_optional(f"Odometer in km [{vehicle.odometer}] (cannot decrease): ",
                            vehicle.check_odometer)

    updated = center.update_vehicle(vehicle.reg_no, new_reg_no, owner, model, year, odometer)
    save_data(center)
    print(f"\nUpdated: {updated}. Its service history is still linked to it.")


def delete_vehicle(center):
    vehicle = ask_vehicle(center, "Registration number of the vehicle to delete: ")
    count = len(center.get_history(vehicle.reg_no))
    print(f"\nThis will permanently delete {vehicle} and its {count} service record(s).")
    if input("Type YES to confirm: ").strip().upper() != "YES":
        print("Deletion cancelled. Nothing was changed.")
        return
    center.delete_vehicle(vehicle.reg_no)
    save_data(center)
    print("Vehicle and its service history deleted.")


def record_service(center):
    print("\n--- Record a vehicle service ---")
    vehicle = ask_vehicle(center)
    print(f"{vehicle} - odometer {vehicle.odometer} km, "
          f"last service: {last_service_text(vehicle)}")
    service_date = ask("Service date (YYYY-MM-DD, Enter = today): ",
                       vehicle.check_service_date, date.today())
    odometer = ask("Odometer at service (km): ", vehicle.check_odometer)
    service_type = ask(f"Service type ({'/'.join(SERVICE_TYPES)}): ", validate_service_type)
    work_done = ask("Work performed: ", validate_text)
    parts_cost = ask(f"Parts cost ({CURRENCY}): ", validate_cost)
    suggested = center.estimate_labour(vehicle, service_type)
    labour_cost = ask(f"Labour cost ({CURRENCY}) [Enter = {suggested:,.2f} by rate card]: ",
                      validate_cost, suggested)

    record = center.add_service(vehicle.reg_no, service_date, odometer, service_type,
                                work_done, parts_cost, labour_cost)
    save_data(center)
    print(f"\nService #{record.service_id} recorded. Total cost: {money(record.total_cost)}")


def show_history(center):
    vehicle = ask_vehicle(center)
    records = center.get_history(vehicle.reg_no)
    if not records:
        print(f"\nNo service history for {vehicle}.")
        return
    print(f"\n--- Service history for {vehicle} ---")
    print_history_table(records)
    print(f"Total spent on this vehicle: {money(sum(r.total_cost for r in records))}")


def show_service_charges(center):
    print("\n--- Service charge calculator ---")
    vehicle = ask_vehicle(center)
    print(f"Labour rate card for {vehicle}:")
    for service_type in SERVICE_TYPES:
        print(f"  {service_type:<8}{money(center.estimate_labour(vehicle, service_type))}")
    service_type = ask(f"Service type ({'/'.join(SERVICE_TYPES)}): ", validate_service_type)
    parts_cost = ask(f"Expected parts cost ({CURRENCY}): ", validate_cost)
    labour = center.estimate_labour(vehicle, service_type)
    print(f"\nEstimate for a {service_type} service:")
    print(f"  Labour charge : {money(labour)}")
    print(f"  Parts cost    : {money(parts_cost)}")
    print(f"  Total         : {money(labour + parts_cost)}")


def show_due_vehicles(center):
    print("\nReminder rules used (set in rules.py; simple demo rules, NOT manufacturer advice):")
    for line in center.policy_description():
        print(f"  {line}")
    due = center.vehicles_due()
    if not due:
        print("\nNo vehicles are due for maintenance.")
        return
    print(f"\n--- {len(due)} vehicle(s) due for maintenance ---")
    for vehicle, reasons in due:
        print(f"\n{vehicle} - owner: {vehicle.owner}")
        for reason in reasons:
            print(f"    * {reason}")


def show_summary(center):
    report = center.summary()
    counts, revenue = report["vehicle_counts"], report["revenue"]
    total_revenue = revenue["car"] + revenue["bike"]
    average = total_revenue / report["service_count"] if report["service_count"] else 0
    print("\n===== SUMMARY REPORT =====")
    print(f"Registered vehicles : {counts['car'] + counts['bike']} "
          f"(cars: {counts['car']}, bikes: {counts['bike']})")
    print(f"Services recorded   : {report['service_count']}")
    print(f"Parts total         : {money(report['parts_total'])}")
    print(f"Labour total        : {money(report['labour_total'])}")
    print(f"Revenue from cars   : {money(revenue['car'])}")
    print(f"Revenue from bikes  : {money(revenue['bike'])}")
    print(f"Total revenue       : {money(total_revenue)}")
    print(f"Average per service : {money(average)}")
    print(f"Vehicles due        : {report['due_count']}")


# ---------- menu ----------
MENU_TEXT = """
========== VEHICLE SERVICE & MAINTENANCE SYSTEM ==========
 1. Register a new vehicle
 2. Display all registered vehicles
 3. Search for a vehicle by registration number
 4. Update vehicle details
 5. Delete a vehicle
 6. Record a vehicle service
 7. Display service history for a vehicle
 8. Calculate and display service charges
 9. Display vehicles due for maintenance
10. Display a summary report
11. Save data and exit
12. Export vehicle and service data to Excel"""

ACTIONS = {
    "1": register_vehicle, "2": show_all_vehicles, "3": search_vehicle, "4": update_vehicle,
    "5": delete_vehicle, "6": record_service, "7": show_history, "8": show_service_charges,
    "9": show_due_vehicles, "10": show_summary, "12": export_to_excel,
}


def run_menu(center):
    while True:
        print(MENU_TEXT)
        choice = input("Enter your choice (1-12): ").strip()
        if choice == "11":
            return
        action = ACTIONS.get(choice)
        if action is None:
            print("Invalid choice. Please enter a number from 1 to 12.")
            continue
        try:
            action(center)
        except (ValueError, ServiceCenterError) as error:
            print(f"\nError: {error}")


def main():
    data_folder = Path(__file__).resolve().parent / "data"
    center = ServiceCenter(DataStore(data_folder), MaintenancePolicy())
    try:
        for warning in center.load():
            print(f"WARNING: {warning}")
    except OSError as error:
        print(f"Cannot read the data files ({error}). Exiting so no data is overwritten.")
        return

    try:
        run_menu(center)
    except (KeyboardInterrupt, EOFError):
        print("\nProgram interrupted.")
    save_data(center)
    print("Data saved. Goodbye!")


if __name__ == "__main__":
    main()
