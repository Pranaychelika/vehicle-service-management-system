"""ServiceCenter: manages vehicles and service records and saves/loads them."""

from models import ServiceRecord, create_vehicle, validate_reg_no, validate_service_type

VEHICLES_FILE = "vehicles.json"
SERVICES_FILE = "services.json"


class ServiceCenterError(Exception):
    """Raised when a request breaks a service-center rule (duplicate, unknown vehicle...)."""


class ServiceCenter:
    def __init__(self, store, policy):
        self._store = store
        self._policy = policy
        self._vehicles = {}            # registration number -> Vehicle object
        self._records = []             # ServiceRecord objects, oldest first
        self._next_service_id = 1      # saved in the file so deleted IDs are never reused

    # ---------- vehicles ----------
    def check_reg_no_available(self, reg_no):
        key = validate_reg_no(reg_no)
        if key in self._vehicles:
            raise ServiceCenterError(f"A vehicle with registration number {key} already exists.")

    def register_vehicle(self, vehicle):
        self.check_reg_no_available(vehicle.reg_no)
        self._vehicles[vehicle.reg_no] = vehicle

    def get_vehicle(self, reg_no):
        key = validate_reg_no(reg_no)
        if key not in self._vehicles:
            raise ServiceCenterError(f"No vehicle found with registration number {key}.")
        return self._vehicles[key]

    def all_vehicles(self):
        return [self._vehicles[key] for key in sorted(self._vehicles)]

    def update_vehicle(self, reg_no, new_reg_no=None, owner=None, model=None,
                       year=None, odometer=None):
        """Change details. A new Vehicle is built first, so a bad value changes nothing."""
        old = self.get_vehicle(reg_no)
        if odometer is not None:
            old.check_odometer(odometer)           # odometer may not go down
        details = old.to_dict()
        for name, value in (("reg_no", new_reg_no), ("owner", owner), ("model", model),
                            ("year", year), ("odometer", odometer)):
            if value is not None:
                details[name] = value
        updated = create_vehicle(**details)        # validates every value again

        if updated.reg_no != old.reg_no:
            self.check_reg_no_available(updated.reg_no)
            for record in self._records:           # keep service history linked to the vehicle
                if record.vehicle_reg_no == old.reg_no:
                    record.vehicle_reg_no = updated.reg_no
            del self._vehicles[old.reg_no]
        self._vehicles[updated.reg_no] = updated
        return updated

    def delete_vehicle(self, reg_no):
        """Delete a vehicle AND its service records (so no orphan records remain)."""
        vehicle = self.get_vehicle(reg_no)
        kept = [r for r in self._records if r.vehicle_reg_no != vehicle.reg_no]
        removed = len(self._records) - len(kept)
        self._records = kept
        del self._vehicles[vehicle.reg_no]
        return removed

    # ---------- services ----------
    def estimate_labour(self, vehicle, service_type):
        return self._policy.labour_charge(vehicle, validate_service_type(service_type))

    def add_service(self, reg_no, service_date, odometer, service_type, work_done,
                    parts_cost, labour_cost=None):
        vehicle = self.get_vehicle(reg_no)         # no records for nonexistent vehicles
        if labour_cost is None:
            labour_cost = self.estimate_labour(vehicle, service_type)
        record = ServiceRecord(self._next_service_id, vehicle.reg_no, service_date, odometer,
                               service_type, work_done, parts_cost, labour_cost)
        # record_service checks date and odometer against the vehicle,
        # and raises before changing anything.
        vehicle.record_service(record.service_date, record.odometer)
        self._records.append(record)
        self._next_service_id += 1
        return record

    def get_history(self, reg_no):
        """Records of one vehicle. Dates cannot go backwards, so append order is date order."""
        vehicle = self.get_vehicle(reg_no)
        return [r for r in self._records if r.vehicle_reg_no == vehicle.reg_no]

    def all_services(self):
        return list(self._records)

    # ---------- reports ----------
    def vehicles_due(self):
        due = []
        for vehicle in self.all_vehicles():
            reasons = self._policy.check_due(vehicle)
            if reasons:
                due.append((vehicle, reasons))
        return due

    def policy_description(self):
        return self._policy.describe()

    def summary(self):
        vehicle_counts = {"car": 0, "bike": 0}
        for vehicle in self._vehicles.values():
            vehicle_counts[vehicle.get_type()] += 1

        revenue = {"car": 0.0, "bike": 0.0}
        parts_total = labour_total = 0.0
        for record in self._records:
            vehicle_type = self._vehicles[record.vehicle_reg_no].get_type()
            revenue[vehicle_type] += record.total_cost
            parts_total += record.parts_cost
            labour_total += record.labour_cost
        return {
            "vehicle_counts": vehicle_counts,
            "service_count": len(self._records),
            "revenue": revenue,
            "parts_total": parts_total,
            "labour_total": labour_total,
            "due_count": len(self.vehicles_due()),
        }

    # ---------- saving and loading ----------
    def save(self):
        vehicles = [vehicle.to_dict() for vehicle in self._vehicles.values()]
        services = {"next_service_id": self._next_service_id,
                    "records": [record.to_dict() for record in self._records]}
        self._store.save(VEHICLES_FILE, vehicles)
        self._store.save(SERVICES_FILE, services)

    def load(self):
        """Load both files. Returns a list of warning messages (empty if all is well)."""
        warnings = []
        vehicle_data, warning = self._store.load(VEHICLES_FILE, [])
        if warning:
            warnings.append(warning)
        service_data, warning = self._store.load(SERVICES_FILE, {})
        if warning:
            warnings.append(warning)

        skipped = 0
        for item in vehicle_data:
            try:
                vehicle = create_vehicle(**item)
                self.check_reg_no_available(vehicle.reg_no)
                self._vehicles[vehicle.reg_no] = vehicle
            except (KeyError, TypeError, ValueError, ServiceCenterError) as error:
                skipped += 1
                warnings.append(f"Skipped an invalid vehicle record: {error}")

        for item in service_data.get("records", []):
            try:
                record = ServiceRecord.from_dict(item)
                if record.vehicle_reg_no not in self._vehicles:
                    raise ValueError(f"service {record.service_id} refers to unknown vehicle "
                                     f"{record.vehicle_reg_no}")
                self._records.append(record)
            except (KeyError, TypeError, ValueError) as error:
                skipped += 1
                warnings.append(f"Skipped an invalid service record: {error}")

        saved_id = service_data.get("next_service_id", 1)
        if not isinstance(saved_id, int):
            saved_id = 1
        highest_id = max((r.service_id for r in self._records), default=0)
        self._next_service_id = max(saved_id, highest_id + 1)

        if skipped:                    # keep the original files so nothing is lost for good
            for filename in (VEHICLES_FILE, SERVICES_FILE):
                self._store.backup(filename)
            warnings.append("Copies of the original data files were saved "
                            "(file names containing '_backup_').")
        return warnings
