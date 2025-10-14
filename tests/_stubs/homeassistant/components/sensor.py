from enum import Enum


class SensorDeviceClass(Enum):
    TEMPERATURE = "temperature"
    SIGNAL_STRENGTH = "signal_strength"


class SensorStateClass(Enum):
    MEASUREMENT = "measurement"


class SensorEntity:
    pass
