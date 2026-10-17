
from pathlib import Path

import pandas as pd


def export_to_excel(center):
    """Export vehicle and service records to an Excel workbook."""

    vehicles = [vehicle.to_dict() for vehicle in center.all_vehicles()]

    services = [
        record.to_dict()
        for record in center.all_services()
    ]

    vehicles_df = pd.DataFrame(vehicles)
    services_df = pd.DataFrame(services)

    output_file = Path(__file__).resolve().parent / "vehicle_service_report.xlsx"

    try:
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            vehicles_df.to_excel(writer, sheet_name="Vehicles", index=False)
            services_df.to_excel(writer, sheet_name="Service History", index=False)

        print(f"\nExcel report exported successfully: {output_file}")

    except PermissionError:
        print("\nPlease close the Excel report if it is open, then try again.")
    except OSError as error:
        print(f"\nCould not export the report: {error}")
