# 导入 MicroPython 的 Pin 和 Timer 模块
from machine import Pin, Timer


class Button:
    def __init__(self, pin_num, idle_state, debounce_time=50, press_callback=None, release_callback=None):
        """
        初始化按键类
        :param pin_num: 引脚编号
        :param idle_state: 空闲状态电平 (1=高电平, 0=低电平)
        :param debounce_time: 防抖时间(毫秒)
        :param press_callback: 按键按下回调函数
        :param release_callback: 按键释放回调函数
        """
        self.debounce_time = debounce_time
        self.press_callback = press_callback
        self.release_callback = release_callback
        self.idle_state = idle_state

        # 配置上拉/下拉电阻.空闲状态是高电平(1):上拉电阻;是低电平(0):下拉电阻
        pull = Pin.PULL_UP if idle_state == 1 else Pin.PULL_DOWN
        self.pin = Pin(pin_num, Pin.IN, pull)

        # 初始化状态,将最后一次稳定的引脚状态初始化为当前引脚值
        self.last_stable_state = self.pin.value()
        self.debounce_timer = None    # 防抖定时器

        # 配置双边缘触发中断
        self.pin.irq(     # 配置中断回调
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=self._irq_handler  # 中断服务程序,实时响应硬件事件
        )

    def _irq_handler(self, pin):
        """中断处理函数"""
        if self.debounce_timer:
            self.debounce_timer.deinit()  # 如果已有防抖定时器在运行，先停止它

        self.debounce_timer = Timer(-1)  # 创建一个新的定时器(使用虚拟定时器 -1)
        self.debounce_timer.init(
            period=self.debounce_time,  # 设置定时时间为防抖时间
            mode=Timer.ONE_SHOT,  # 初始化定时器为单次模式(ONE_SHOT)
            callback=lambda t: self._debounce_handler()  # 定时器到期时调用 _debounce_handler 函数
        )

    def _debounce_handler(self):
        """防抖处理函数"""
        current_value = self.pin.value()  # 获取当前引脚值
        if current_value != self.last_stable_state:  # 如果当前值与上次稳定状态不同，说明有有效变化
            # 状态变化有效
            if current_value == self.idle_state:
                if self.release_callback:  # 如果当前值等于空闲状态，调用释放回调函数
                    self.release_callback()
            else:
                if self.press_callback:
                    self.press_callback()  # 调用按下回调函数
                # 更新稳定状态记录
            self.last_stable_state = current_value  # 更新最后一次稳定的引脚状态
        self.debounce_timer = None  # 将防抖定时器重置为None

    def get_state(self):
        """获取当前稳定状态"""
        # 返回当前稳定状态是否不等于空闲状态，
        # 如果不等，表示按键被按下(返回 True)，
        # 如果相等，表示按键被释放(返回 False)
        return self.last_stable_state != self.idle_state


# 回调函数定义
def on_press():
    print("按键按下")


def on_release():
    print("按键松开")


# 初始化按键实例（引脚号，空闲电平，防抖时间，回调函数）
button = Button(
    pin_num=15,
    idle_state=1,  # 高电平为空闲
    debounce_time=30,
    press_callback=on_press,
    release_callback=on_release
)

# 主循环
while True:
    if button.get_state():
        print("当前状态：按下")
    else:
        print("当前状态：松开")