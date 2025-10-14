class HomeAssistant:
    def __init__(self):
        self.config = type("C", (), {"units": type("U", (), {"temperature_unit": "°C"})})()
