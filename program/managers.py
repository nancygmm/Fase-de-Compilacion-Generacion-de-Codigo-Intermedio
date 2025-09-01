class TempManager:
    def __init__(self):
        self.counter = 0
        self.free = []

    def new_temp(self):
        if self.free:
            return self.free.pop()
        self.counter += 1
        return f"t{self.counter}"

    def release_temp(self, t):
        self.free.append(t)

class LabelManager:
    def __init__(self):
        self.counter = 0

    def new_label(self):
        self.counter += 1
        return f"L{self.counter}"
