from dataclasses import dataclass


@dataclass
class DeviceInfo:
    identifiers: set
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    via_device: str | None = None
