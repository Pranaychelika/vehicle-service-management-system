"""DataStore: reads and writes the JSON files safely."""

import json
from datetime import datetime
from pathlib import Path


class DataStore:
    def __init__(self, folder):
        self._folder = Path(folder)

    def load(self, filename, default):
        """Return (data, warning). A missing file is normal on the first run."""
        path = self._folder / filename
        if not path.exists():
            return default, None
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except ValueError:          # json.JSONDecodeError is a kind of ValueError
            data = None
        if not isinstance(data, type(default)):
            backup = self.backup(filename)
            return default, (f"{filename} is damaged or has an unexpected layout. "
                             f"A copy was kept as {backup.name}; starting with empty data.")
        return data, None

    def save(self, filename, data):
        """Write to a temporary file first, then swap it in, so a crash cannot corrupt old data."""
        self._folder.mkdir(parents=True, exist_ok=True)
        path = self._folder / filename
        temp_path = path.with_name(path.name + ".tmp")
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
        temp_path.replace(path)

    def backup(self, filename):
        """Copy a file to a time-stamped backup name. Returns the backup path (None if no file)."""
        path = self._folder / filename
        if not path.exists():
            return None
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_name(f"{path.stem}_backup_{stamp}{path.suffix}")
        backup_path.write_bytes(path.read_bytes())
        return backup_path
