class DataUpdateCoordinator:
    def __init__(self):
        self.data = None

    def async_add_listener(self, _cb):
        # no-op for tests
        pass


class CoordinatorEntity:
    def __init__(self, coordinator: DataUpdateCoordinator):
        self.coordinator = coordinator
