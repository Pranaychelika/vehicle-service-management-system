"""Configurable rules for maintenance reminders and service charges.

Change the numbers in DEFAULT_RULES to change how the whole program behaves.
These are simple demonstration rules, NOT manufacturer recommendations.
"""

from datetime import date

CURRENCY = "Rs."
SERVICE_TYPES = ("basic", "full", "repair")

DEFAULT_RULES = {
    "car": {
        "interval_km": 10000,          # due after this many km since last service...
        "interval_days": 180,          # ...or after this many days
        "labour": {"basic": 1500.0, "full": 3500.0, "repair": 2500.0},
        "old_vehicle_years": 10,       # cars older than this pay a surcharge
        "old_vehicle_surcharge": 0.10,  # 10 % extra labour
    },
    "bike": {
        "interval_km": 3000,
        "interval_days": 90,
        "labour": {"basic": 400.0, "full": 900.0, "repair": 600.0},
        "chain_care_fee": 150.0,       # flat fee added to every "full" service
    },
}


class MaintenancePolicy:
    """Holds the rules and answers: is a vehicle due? what is the labour charge?"""

    def __init__(self, rules=None):
        self._rules = rules if rules is not None else DEFAULT_RULES

    def rules_for(self, vehicle):
        return self._rules[vehicle.get_type()]

    def labour_charge(self, vehicle, service_type):
        # Polymorphism: Car and Bike each calculate this in their own way.
        return vehicle.labour_charge(service_type, self.rules_for(vehicle))

    def check_due(self, vehicle, today=None):
        """Return a list of reasons why the vehicle is due (empty list = not due)."""
        today = today or date.today()
        rules = self.rules_for(vehicle)
        reasons = []

        if vehicle.last_service_odometer is None:
            # Assumption: never serviced here, so count kilometres from zero.
            km_since = vehicle.odometer
            source = "No service on record,"
        else:
            km_since = vehicle.odometer - vehicle.last_service_odometer
            source = "Since last service:"
        if km_since >= rules["interval_km"]:
            reasons.append(f"{source} {km_since} km driven (limit {rules['interval_km']} km)")

        if vehicle.last_service_date is not None:
            days_since = (today - vehicle.last_service_date).days
            if days_since >= rules["interval_days"]:
                reasons.append(f"Last service was {days_since} days ago "
                               f"(limit {rules['interval_days']} days)")
        return reasons

    def describe(self):
        """Readable summary of the reminder rules, for display."""
        return [f"{name.title()}: every {rule['interval_km']} km or {rule['interval_days']} days"
                for name, rule in self._rules.items()]
