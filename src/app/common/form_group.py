class FormControl:
    def __init__(self, value=None):
        self.value = value
        self.errors = []

    def is_valid(self):
        return not self.errors


class FormGroup:
    def __init__(self, controls: dict):
        self.controls = controls

    def is_valid(self):
        return all(control.is_valid() for control in self.controls.values())

    def get(self, key):
        return self.controls.get(key)
