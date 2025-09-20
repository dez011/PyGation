class MockGPIO:
    BCM = 'BCM'
    OUT = 'OUT'
    IN = 'IN'
    HIGH = 'HIGH'
    LOW = 'LOW'

    @staticmethod
    def setmode(mode):
        print(f"MOCK GPIO mode set to {mode}")

    @staticmethod
    def setup(channel, mode):
        print(f"MOCK GPIO channel {channel} set up as {mode}")

    @staticmethod
    def output(channel, state):
        print(f"MOCK GPIO channel {channel} output set to {state}")

    def input(self, channel):
        return self.LOW

    @staticmethod
    def cleanup():
        print("MOCK GPIO cleanup called")
