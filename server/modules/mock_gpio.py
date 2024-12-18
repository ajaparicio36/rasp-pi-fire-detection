class GPIO:
    """Mock GPIO class for development environments"""
    BCM = 'BCM'
    BOARD = 'BOARD'
    IN = 'IN'
    OUT = 'OUT'
    HIGH = 1
    LOW = 0
    PUD_DOWN = 'PUD_DOWN'
    PUD_UP = 'PUD_UP'
    BOTH = 'BOTH'

    @staticmethod
    def setmode(mode):
        print(f"GPIO.setmode({mode})")

    @staticmethod
    def setup(pin, mode, pull_up_down=None):
        pull_up_down_str = f", pull_up_down={pull_up_down}" if pull_up_down else ""
        print(f"GPIO.setup({pin}, {mode}{pull_up_down_str})")

    @staticmethod
    def output(pin, value):
        print(f"GPIO.output({pin}, {value})")

    @staticmethod
    def input(pin):
        print(f"GPIO.input({pin})")
        return 0  # Mock return value

    @staticmethod
    def add_event_detect(pin, edge, callback=None, bouncetime=None):
        print(f"GPIO.add_event_detect({pin}, {edge}, callback={callback.__name__}, bouncetime={bouncetime})")

    @staticmethod
    def cleanup(pins=None):
        pins_str = str(pins) if pins else "all pins"
        print(f"GPIO.cleanup({pins_str})")