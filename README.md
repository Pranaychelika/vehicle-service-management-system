# Vehicle Service & Maintenance Management System

## 1. Project Overview

The Vehicle Service & Maintenance Management System is a Python-based, menu-driven application designed to manage vehicle registration, service records, maintenance reminders, and service cost calculations.

The project uses Object-Oriented Programming (OOP) to organize vehicle and service information. JSON files are used for local data storage, and Pandas with OpenPyXL is used to export reports to Excel.

## 2. Features

- Register new vehicles (cars and bikes).
- Display all registered vehicles.
- Search for vehicles by registration number.
- Update and delete vehicle details.
- Record vehicle service details and costs.
- View service history for individual vehicles.
- Calculate estimated service charges.
- Identify vehicles due for maintenance.
- Generate a summary report with vehicle counts and service revenue.
- Save vehicle and service records in JSON files.
- Export vehicle and service records to an Excel workbook.

## 3. Technologies Used

- **Programming Language:** Python
- **Concepts:** Object-Oriented Programming (OOP), functions, exception handling, file handling
- **Data Storage:** JSON
- **Data Analysis and Export:** Pandas
- **Excel File Support:** OpenPyXL
- **Development Environment:** Visual Studio Code
- **Version Control:** Git and GitHub

## 4. Project Structure

```text
vehicle_service_system/
├── main.py
├── models.py
├── rules.py
├── sample_data.py
├── service_center.py
├── storage.py
├── export_data.py
├── README.md
├── .gitignore
└── data/
    ├── vehicles.json
    └── services.json
```

The `data/` folder is created locally when the application stores its data. Personal data files and generated Excel reports are excluded from GitHub.

## 5. Requirements

- Python 3.10 or later recommended
- Pandas
- OpenPyXL

Install the required external libraries using:

```bash
python -m pip install pandas openpyxl
```

## 6. How to Run the Project

1. Download or clone this repository.
2. Open the project folder in Visual Studio Code.
3. Open a terminal in the project folder.
4. Install the required libraries.
5. Run the application:

```bash
python main.py
```

6. Select an option from the menu and follow the instructions displayed in the terminal.

## 7. Data Storage and Excel Export

Vehicle information and service history are stored locally in JSON files inside the `data/` folder.

The application can export vehicle and service records to an Excel workbook named `vehicle_service_report.xlsx`. Select option 12 from the application menu to generate the report.

## 8. Limitations

- This is a local, terminal-based academic project.
- The application does not currently use an online database or multi-user login system.
- Maintenance reminders use demonstration rules and should not replace manufacturer-recommended maintenance schedules.

## 9. Team Contributions

Update this section with the actual project team members and their contributions.

- **Project development:** [Add name and contribution]
- **Testing:** [Add name and contribution]
- **Documentation:** [Add name and contribution]

## 10. Future Enhancements

- Develop a graphical user interface or web application.
- Integrate a database such as MySQL.
- Add user authentication and role-based access.
- Add automated maintenance notifications.
- Generate more detailed reports and analytics.
