class MockGPIO:
    BCM = 'BCM'
    OUT = 'OUT'
    IN = 'IN'
    HIGH = 'HIGH'
    LOW = 'LOW'

    def setmode(self, mode):
        print(f"GPIO mode set to {mode}")

    def setup(self, channel, mode):
        print(f"GPIO channel {channel} set up as {mode}")

    def output(self, channel, state):
        print(f"GPIO channel {channel} output set to {state}")

    def input(self, channel):
        return self.LOW

    def cleanup(self):
        print("GPIO cleanup called")
