class AddonManager:
    def __init__(self):
        self.addons = []

    def add(self, addon):
        self.addons.append(addon)

    def remove(self, addon):
        if addon in self.addons:
            self.addons.remove(addon)