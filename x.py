def x():
    import RPi.GPIO as GPIO
    import time

    class Hx711:
        def __init__(self):
            self.SCK = 31    # 物理引脚第11号，时钟
            self.DT = 29     # 物理引脚第13号，数据
            self.flag = 1    # 用于首次读数校准
            self.initweight = 0  # 毛皮
            self.weight = 0      # 测重
            self.delay = 0.09    # 延迟时间

        def setup(self):
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)  # Numbers GPIOs by physical location
            GPIO.setup(self.SCK, GPIO.OUT)  # Set pin's mode is output
            GPIO.setup(self.DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        def start(self):
            GPIO.output(self.SCK, 0)
            value = 0
            while GPIO.input(self.DT):
                time.sleep(self.delay)
            for i in range(24):
                GPIO.output(self.SCK, 1)
                value = value << 1
                GPIO.output(self.SCK, 0)
                if GPIO.input(self.DT) == 1:
                    value += 1
            GPIO.output(self.SCK, 1)
            GPIO.output(self.SCK, 0)
            value = int(value / 1905)
            if self.flag == 1:
                self.flag = 0
                self.initweight = value
            else:
                self.weight = abs(value - self.initweight)
            return self.weight

    def setup_led():
        GPIO.setup(17, GPIO.OUT)  # 红色LED
        GPIO.setup(27, GPIO.OUT)  # 绿色LED

    def turn_on_red():
        GPIO.output(17, True)
        GPIO.output(27, False)

    def turn_on_green():
        GPIO.output(17, False)
        GPIO.output(27, True)

    def check_weight_and_light_led():
        hx711 = Hx711()
        hx711.setup()
        setup_led()
        try:
            while True:
                weight = hx711.start()
                if weight > 200:
                    turn_on_red()
                else:
                    turn_on_green()
                time.sleep(1)  # 每秒检查一次重量
        except KeyboardInterrupt:
            GPIO.cleanup()

    check_weight_and_light_led()