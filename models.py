"""Data classes: Vehicle (abstract), Car, Bike and ServiceRecord, plus input validators."""

import math
from abc import ABC, abstractmethod
from datetime import date, datetime

from rules import SERVICE_TYPES

DATE_FORMAT = "%Y-%m-%d"
VEHICLE_TYPES = ("car", "bike")
EARLIEST_YEAR = 1950


# ---------- Validators: return a clean value, or raise ValueError ----------
def validate_text(value, field="Text"):
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} cannot be empty.")
    return text


def validate_reg_no(value):
    # Spaces and hyphens are removed so "ts 09-ab 1234" and "TS09AB1234" are the same vehicle.
    text = str(value).replace(" ", "").replace("-", "").upper()
    if not (text.isascii() and text.isalnum()):
        raise ValueError("Registration number must be letters and digits only (cannot be empty).")
    return text


def _to_int(value, field):
    try:
        return int(str(value).strip())
    except ValueError:
        raise ValueError(f"{field} must be a whole number.")


def validate_year(value):
    year = _to_int(value, "Year")
    if not EARLIEST_YEAR <= year <= date.today().year:
        raise ValueError(f"Year must be between {EARLIEST_YEAR} and {date.today().year}.")
    return year


def validate_odometer(value):
    km = _to_int(value, "Odometer reading")
    if km < 0:
        raise ValueError("Odometer reading cannot be negative.")
    return km


def validate_cost(value):
    try:
        cost = float(str(value).strip())
    except ValueError:
        raise ValueError("Cost must be a number.")
    if not math.isfinite(cost) or cost < 0:
        raise ValueError("Cost must be zero or more.")
    return round(cost, 2)


def validate_date(value):
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), DATE_FORMAT).date()
    except ValueError:
        raise ValueError("Date must be a real date in YYYY-MM-DD format (e.g. 2026-03-15).")


def _validate_choice(value, options, field):
    choice = str(value).strip().lower()
    if choice not in options:
        raise ValueError(f"{field} must be one of: {', '.join(options)}.")
    return choice


def validate_vehicle_type(value):
    return _validate_choice(value, VEHICLE_TYPES, "Vehicle type")


def validate_service_type(value):
    return _validate_choice(value, SERVICE_TYPES, "Service type")


# ---------- Vehicle classes ----------
class Vehicle(ABC):
    """Abstract base class: common data and behaviour of every vehicle."""

    def __init__(self, reg_no, owner, model, year, odometer,
                 last_service_date=None, last_service_odometer=None):
        # Every value goes through a validating setter or validator (encapsulation).
        self.reg_no = reg_no
        self.owner = owner
        self.model = model
        self.year = year
        self._odometer = 0              # start at 0 so the first value passes the check
        self.odometer = odometer
        self._last_service_date = None
        self._last_service_odometer = None
        if (last_service_date is None) != (last_service_odometer is None):
            raise ValueError("Last service date and odometer must be given together.")
        if last_service_date is not None:
            service_date = self.check_service_date(last_service_date)
            service_odometer = validate_odometer(last_service_odometer)
            if service_odometer > self._odometer:
                raise ValueError("Last service odometer cannot be higher than the current one.")
            self._last_service_date = service_date
            self._last_service_odometer = service_odometer

    # --- abstract methods: every subclass MUST override these ---
    @abstractmethod
    def get_type(self):
        """Return 'car' or 'bike'."""

    @abstractmethod
    def labour_charge(self, service_type, rules):
        """Return the labour charge for this kind of vehicle."""

    # --- properties (getters and validating setters) ---
    @property
    def reg_no(self):
        return self._reg_no

    @reg_no.setter
    def reg_no(self, value):
        self._reg_no = validate_reg_no(value)

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, value):
        self._owner = validate_text(value, "Owner name")

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        self._model = validate_text(value, "Model")

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        self._year = validate_year(value)

    @property
    def odometer(self):
        return self._odometer

    @odometer.setter
    def odometer(self, value):
        self._odometer = self.check_odometer(value)

    @property
    def last_service_date(self):        # read-only: only record_service() may change it
        return self._last_service_date

    @property
    def last_service_odometer(self):    # read-only
        return self._last_service_odometer

    # --- checks that can be used before changing anything ---
    def check_odometer(self, value):
        """Return the odometer value as an int, or raise ValueError if it would go down."""
        km = validate_odometer(value)
        if km < self._odometer:
            raise ValueError(f"Odometer cannot decrease (current reading is {self._odometer} km).")
        return km

    def check_service_date(self, value):
        """Return a valid service date, or raise ValueError."""
        service_date = validate_date(value)
        if service_date > date.today():
            raise ValueError("Service date cannot be in the future.")
        if service_date.year < self._year:
            raise ValueError("Service date cannot be before the manufacturing year.")
        if self._last_service_date is not None and service_date < self._last_service_date:
            raise ValueError("Service date cannot be earlier than the last service "
                             f"({self._last_service_date}).")
        return service_date

    # --- behaviour ---
    def record_service(self, service_date, service_odometer):
        """Update 'last service' details. Everything is checked before anything is changed."""
        service_date = self.check_service_date(service_date)
        service_odometer = self.check_odometer(service_odometer)
        self._last_service_date = service_date
        self._last_service_odometer = service_odometer
        self._odometer = service_odometer

    def age(self):
        return date.today().year - self._year

    def to_dict(self):
        """Convert to a plain dictionary that can be saved as JSON."""
        last_date = self._last_service_date.isoformat() if self._last_service_date else None
        return {
            "vehicle_type": self.get_type(),
            "reg_no": self._reg_no,
            "owner": self._owner,
            "model": self._model,
            "year": self._year,
            "odometer": self._odometer,
            "last_service_date": last_date,
            "last_service_odometer": self._last_service_odometer,
        }

    def __str__(self):
        return f"{self._reg_no} ({self.get_type().title()} - {self._model})"


class Car(Vehicle):
    def get_type(self):
        return "car"

    def labour_charge(self, service_type, rules):
        charge = rules["labour"][service_type]
        if self.age() > rules["old_vehicle_years"]:       # older cars cost more to work on
            charge = charge * (1 + rules["old_vehicle_surcharge"])
        return round(charge, 2)


class Bike(Vehicle):
    def get_type(self):
        return "bike"

    def labour_charge(self, service_type, rules):
        charge = rules["labour"][service_type]
        if service_type == "full":                        # full service includes chain care
            charge = charge + rules["chain_care_fee"]
        return round(charge, 2)


VEHICLE_CLASSES = {"car": Car, "bike": Bike}


def create_vehicle(vehicle_type, **details):
    """Factory: build a Car or a Bike. Also used to rebuild vehicles from saved JSON."""
    vehicle_class = VEHICLE_CLASSES[validate_vehicle_type(vehicle_type)]
    return vehicle_class(**details)


# ---------- Service record ----------
class ServiceRecord:
    """One completed service. Values are validated once, when the record is created."""

    def __init__(self, service_id, vehicle_reg_no, service_date, odometer,
                 service_type, work_done, parts_cost, labour_cost):
        self._service_id = _to_int(service_id, "Service ID")
        if self._service_id < 1:
            raise ValueError("Service ID must be 1 or more.")
        self.vehicle_reg_no = vehicle_reg_no
        self._service_date = validate_date(service_date)
        self._odometer = validate_odometer(odometer)
        self._service_type = validate_service_type(service_type)
        self._work_done = validate_text(work_done, "Work performed")
        self._parts_cost = validate_cost(parts_cost)
        self._labour_cost = validate_cost(labour_cost)

    @property
    def service_id(self):
        return self._service_id

    @property
    def vehicle_reg_no(self):
        return self._vehicle_reg_no

    @vehicle_reg_no.setter
    def vehicle_reg_no(self, value):      # needed when a vehicle's registration number is changed
        self._vehicle_reg_no = validate_reg_no(value)

    @property
    def service_date(self):
        return self._service_date

    @property
    def odometer(self):
        return self._odometer

    @property
    def service_type(self):
        return self._service_type

    @property
    def work_done(self):
        return self._work_done

    @property
    def parts_cost(self):
        return self._parts_cost

    @property
    def labour_cost(self):
        return self._labour_cost

    @property
    def total_cost(self):
        # Calculated, never stored separately, so it can never disagree with its parts.
        return round(self._parts_cost + self._labour_cost, 2)

    def to_dict(self):
        return {
            "service_id": self._service_id,
            "vehicle_reg_no": self._vehicle_reg_no,
            "service_date": self._service_date.isoformat(),
            "odometer": self._odometer,
            "service_type": self._service_type,
            "work_done": self._work_done,
            "parts_cost": self._parts_cost,
            "labour_cost": self._labour_cost,
            "total_cost": self.total_cost,
        }

    @classmethod
    def from_dict(cls, data):
        fields = dict(data)
        fields.pop("total_cost", None)    # recalculated, so the saved copy is ignored
        return cls(**fields)
