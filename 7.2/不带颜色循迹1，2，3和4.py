import cv2
import numpy as np
import 模式匹配数字
import RPi.GPIO as GPIO
import YB_Pcb_Car  # 导入Yahboom专门库文件
import ipywidgets.widgets as widgets
import threading
import enum
from tensorflow.keras.models import load_model
from IPython.display import display, Image
import ipywidgets as widgets
from IPython.display import clear_output
import time
import tensorflow as tf
import 蓝牙发送

"""
    ******************************
    有些函数超级长,可以在vscode折叠看
    ******************************

"""



car = YB_Pcb_Car.YB_Pcb_Car()
time_turning = 1.05
time_going = 0.2
speed_spin = 190 #转弯速度
speed_go = 50 #巡线直行速度


# 循迹红外引脚定义
Tracking_Right1 = 11  # X1A  右边第一个传感器
Tracking_Right2 = 7  # X2A  右边第二个传感器
Tracking_Left1 = 13  # X1B 左边第一个传感器
Tracking_Left2 = 15  # X2B 左边第二个传感器

model = load_model('strong_digit_recognition_model.h5')
i=0
def bgr8_to_jpeg(value, quality=75):
    return bytes(cv2.imencode('.jpg', value)[1])

# 显示摄像头组件
image_widget = widgets.Image(format='jpeg', width=320, height=240)
display(image_widget)

# 定义预处理函数
def preprocess_image(img):
    global i
    # 将图像转换为灰度图像
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 高斯模糊
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # 使用自适应阈值
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    # 找到轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 初始化一个空白的28x28的图像
    digit_img = np.zeros((28, 28), dtype=np.uint8)
    bounding_box = None
    i+=1
    if contours:
        # 找到最大的轮廓
        largest_contour = max(contours, key=cv2.contourArea)
        # 获取轮廓的边界框
        x, y, w, h = cv2.boundingRect(largest_contour)
        # 裁剪边缘，防止误读
        margin = 20
        x = max(x + margin, 0)
        y = max(y + margin, 0)
        w = max(w - 2 * margin, 1)
        h = max(h - 2 * margin, 1)
        # 确保方框的宽高比大致为8:6，避免非数字区域
        if 0.8 * (6/8) < w/h < 1.2 * (6/8):
            bounding_box = (x, y, w, h)
            # 提取数字并调整大小
            digit = gray[y:y+h, x:x+w]
            # 透视变换校正
            pts1 = np.float32([[x, y], [x+w, y], [x, y+h], [x+w, y+h]])
            pts2 = np.float32([[0, 0], [28, 0], [0, 21], [28, 21]])  # 28:21 is the same as 8:6 ratio
            M = cv2.getPerspectiveTransform(pts1, pts2)
            digit = cv2.warpPerspective(gray, M, (28, 21))
            # 调整为 28x28
            digit_img = cv2.resize(digit, (28, 28), interpolation=cv2.INTER_AREA)
            # 反色（因为MNIST数据集中的数字是白色背景黑色字）
            digit_img = cv2.bitwise_not(digit_img)
    # 归一化处理
    normalized = digit_img / 255.0
    # 添加批次维度
    reshaped = np.reshape(normalized, (1, 28, 28, 1))
    return reshaped, bounding_box, digit_img, largest_contour

# 计算曲率的方法
def calculate_curvature(contour):
    curvatures = []
    for i in range(1, len(contour) - 1):
        pt1 = contour[i - 1][0]
        pt2 = contour[i][0]
        pt3 = contour[i + 1][0]
        # 计算两个向量
        v1 = pt1 - pt2
        v2 = pt3 - pt2
        # 计算两个向量的夹角余弦值
        cosine_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        # 计算曲率
        curvature = 1 - cosine_angle
        curvatures.append(curvature)
    return np.mean(curvatures)


def reco():
 global i
 one = 0
 two = 0
 three = 0
 four = 0
 five = 0
 six = 0
 seven = 0
 eight = 0
 while True:
    # 读取帧
    ret, frame = cap.read()
    if not ret:
        break

    # 对帧进行预处理
    processed, bbox, digit_img, contour = preprocess_image(frame)

    # 使用模型进行预测
    prediction = model.predict(processed)
    digit = np.argmax(prediction)

    # 处理印刷体1和7的识别问题
    if digit == 7 and contour is not None:
        # 进一步检查曲率
        curvature = calculate_curvature(contour)
        print(curvature)
        if curvature < 1.675:  # 根据实际情况调整阈值
            digit = 1

    if digit == 0 and contour is not None:
        digit = 4

    # 在帧上显示预测结果
    cv2.putText(frame, f'Digit: {digit}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    image_widget.value = bgr8_to_jpeg(frame)
    # 如果检测到方框，圈起来
    if bbox is not None:
        x, y, w, h = bbox
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # 显示带预测结果的帧
    # 显示识别的图像
    if(digit == 1):
        one+=1
    elif(digit == 2):
        two+=1
    elif(digit == 3):
        three+=1
    elif(digit == 4):
        four+=1
    elif(digit == 5):
        five+=1
    elif(digit == 6):
        six+=1
    elif(digit == 7):
        seven+=1
    elif(digit == 8):
        eight+=1
    # 按q键退出循环
    if i>30:
        counts = [one, two, three, four, five, six, seven, eight]
        print(counts)
        max_count = max(counts)
        max_digit = counts.index(max_count) + 1  # 加1是因为列表索引从0开始，而数字从1开始
        one,two,three,four,five,six,seven,eight,i = 0,0,0,0,0,0,0,0,0
        return max_digit

def setup_gpio():
    # 设置GPIO口为BCM编码方式
    GPIO.setmode(GPIO.BOARD)

    # 忽略警告信息
    GPIO.setwarnings(False)

    GPIO.setup(Tracking_Left1, GPIO.IN)
    GPIO.setup(Tracking_Left2, GPIO.IN)
    GPIO.setup(Tracking_Right1, GPIO.IN)
    GPIO.setup(Tracking_Right2, GPIO.IN)

def weight(module):
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
            value = int(value / 4)
            if self.flag == 1:
                self.flag = 0
                self.initweight = value
            else:
                self.weight = abs(value - self.initweight)
            return self.weight

    def setup_led():
        GPIO.setup(18, GPIO.OUT)  # 红色LED
        GPIO.setup(22, GPIO.OUT)  # 绿色LED

    def turn_on_red():
        GPIO.output(18, True)
        GPIO.output(22, False)

    def turn_on_green():
        GPIO.output(18, False)
        GPIO.output(22, True)

    def check_weight_and_light_led():
        hx711 = Hx711()
        hx711.setup()
        setup_led()
        time.sleep(1)  # 等待传感器初始化
        try:
            if module == 1:
             while True:
                weight = hx711.start()
                print(weight)
                if weight > 250:
                    turn_on_green()
                    break
                else:
                    turn_on_red()
                time.sleep(1)  # 每秒检查一次重量
            elif module == 2:
                while True:
                    weight = hx711.start()
                    if weight > 250:
                        turn_on_red()
                        break
                    else:
                        turn_on_green()
                    time.sleep(1)
        except KeyboardInterrupt:
            GPIO.cleanup()

    check_weight_and_light_led()


#转头函数，先开转，速度为100，转0.8秒，肯定转不完，再以50的速度转，直到两个传感器都在黑线上，能保证转到位
def turn_180():
    start_time = time.time()
    while True:
        car.Car_Turn_180_(100)
        if (time.time() - start_time >= 1):   
            break
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        car.Car_Turn_180_(50)
        #0xxx或xxx0退出循迹
        if (TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False):
            car.Car_Run(30,30)
            time.sleep(0.01)
            break
    pass

#增加一个函数，在巡线函数中调用，让小车在虚线内部走一段距离，停到合适位置
def runalittle():
    flag = 0
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        car.Car_Run(35,35)
        time.sleep(0.1)
        if flag == 2:
            break
        elif (TrackSensorLeftValue2 == True and TrackSensorRightValue1 == True):
            flag += 1
            
#在巡线函数中调用，用于利用时间控制，走一段带修正的巡线
def runrun(runruntime,speed):
    start_time = time.time()
    print('start')
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        #0xxx或xxx0退出循迹
        if (time.time() - start_time >= runruntime):
            break
        #1001 直行
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
            car.Car_Run(speed, speed)
        # 假路口判断
        #1011   车偏右
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
            car.Car_Left(0, 120)
        #1101   车偏左
        elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
            car.Car_Right(120, 0)
        elif TrackSensorLeftValue1 == True :
            car.Car_Right(180, 0)
        elif TrackSensorRightValue1 == True :
            car.Car_Left(0, 180)

#最后一段路，走到尽头，转180度，摆正重新来过
def end_turn():
    print('wojinlaile')
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        if (TrackSensorLeftValue2 == True and TrackSensorRightValue1 == True):
            turn_180()
            car.Car_Run(60,60)
            time.sleep(0.05)
            car.Car_Stop()
            time.sleep(2)
            break
    #未退出说明假路口
        #1001 直行
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
            car.Car_Run(speed_go, speed_go)
        # 假路口判断
        #1011   车偏右
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
            car.Car_Left(0, 90)
        #1101   车偏左
        elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
            car.Car_Right(90, 0)
        else:
            car.Car_Run(30, 30)

# 循迹部分，停车功能写在这里
def track_line(stop_num,turn_num,num,turn_situation):
    global turn_count
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        #0xxx或xxx0退出循迹
        # 停车代码
        if turn_count == stop_num:
            runrun(2,30)
            runalittle()
            car.Car_Run(60,60)
            time.sleep(0.01)
            car.Car_Stop()
            time.sleep(0.1)
    
            if num == 3 or num == 4:        
                蓝牙发送.send_36(turn_situation)
                
            weight(1)
            turn_180()
            turn_count += 1
            continue
        # 掉头等待代码
        if  turn_count == turn_num:
            runrun(1.4,70)
            turn_180()
            car.Car_Run(70,70)
            time.sleep(0.01)
            car.Car_Stop()
            time.sleep(0.1) #到这里实现掉头并停住
            listen.listen_for_signal() #监听，接收到后退出，继续往下走
            turn_count += 1
            continue
        else:
            if (TrackSensorLeftValue1 == False or TrackSensorRightValue2 == False):
                break
        #未退出说明假路口
            #1001 直行
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
                car.Car_Run(speed_go, speed_go)
            # 假路口判断
            #1011   车偏右
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                car.Car_Left(0, 90)
            #1101   车偏左
            elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                car.Car_Right(90, 0)
            else:
                car.Car_Run(30, 30)

#转弯函数，最开始写的
def turn_at_intersection(direction):
    # 路口转弯
    # 左0 右1 直行2
    start_time = time.time()
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        if direction == 0:
            # 0xxx   左转
            if TrackSensorLeftValue1 == False:
                car.Car_Spin_Left(0, speed_spin)
            # 100x   非左转
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
                car.Car_Run(50, 50)
            # 101x   车偏右
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                car.Car_Left(0, 100)
            # 110x   车偏左
            elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                car.Car_Right(50, 0)

            current_time1 = time.time()
            if current_time1 - start_time >= time_turning:
                break
        elif direction == 1:
            #xxx0
            if TrackSensorRightValue2 == False:
                car.Car_Spin_Right(speed_spin, 0)
            #x001   非右转
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
                car.Car_Run(50, 50)
            #x011   车偏右
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                car.Car_Left(0, 50)
            #x101   车偏左
            elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                car.Car_Right(100, 0)

            current_time2 = time.time()
            if current_time2 - start_time >= time_turning:
                break
        elif direction == 2:
            #x00x直行
            if TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
                car.Car_Run(70, 70)
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                car.Car_Left(0, 70)
            elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                car.Car_Right(70, 0)

            current_time3 = time.time()
            if current_time3 - start_time >= time_going:
                break

try:
    setup_gpio()
    #定义方向，0、1、2用于左转、右转、直行
    l=0
    r=1
    f=2
    run_flag = 0
    turn_count = 1    # 用于跟踪转弯次数
    # 路线规划，走进去、掉头、走出来，与期末时期逻辑相同
    while True:
        num = reco()
        
        if num == 1:
            all_directions = [l,r]
            stop_num = 2
            turn_num = 999 #弃之不用,5678用
            for direction in all_directions: 
                track_line(stop_num,turn_num,num,9999)
                turn_count += 1  # 每次转弯后增加计数
                print('Turning number:', turn_count, 'Direction:', direction)
                turn_at_intersection(direction)
            end_turn()
                
        elif num == 2:
            all_directions = [r,l]
            stop_num = 2
            turn_num = 999 #弃之不用,5678用
            for direction in all_directions: 
                track_line(stop_num,turn_num,num,9999)
                turn_count += 1  # 每次转弯后增加计数
                print('Turning number:', turn_count, 'Direction:', direction)
                turn_at_intersection(direction)
            end_turn()
        
        elif num == 3:
            the_first_direction = 带修正巡线并模式匹配数字.运行() #先高速长时间运行runrun，跳过第一个路口，再低速开摄像头识别到数字返回走法（“l、r”）退出
            if the_first_direction == l    #进去和出去的方向是相关的
                back_turn = r
            elif the_first_direction == r
                back_turn = l
            stop_num = 2 #因为跳过了第一个路口,所以还是2
            turn_num = 999 #弃之不用,5678用
            all_directions = [the_first_direction,back_turn,f]#这是主车，要走到最后，最后一个目前随便写的
            for direction in all_directions: 
                track_line(stop_num,turn_num,num,the_first_direction) #传很多参数,the_first_direction实际是l或者r，要传给从车,让从车知道怎么走
                turn_count += 1  # 每次转弯后增加计数
                print('Turning number:', turn_count, 'Direction:', direction)
                turn_at_intersection(direction)
            end_turn()#也许要换成一个走出去的函数
            '''
                我想是不是可以直接转过第一个弯后runrun(超级长时间,超级大速度)直接走出去,不需要再识别了,但还没有改动,就把f删了,end_turn()换了就好
            '''
            
        elif num == 4:
            the_first_direction = 带修正巡线并模式匹配数字.运行() #先高速长时间运行runrun，跳过第一个路口，再低速开摄像头识别到数字返回走法（“l、r”）退出
            if the_first_direction == l    #进去和出去的方向是相关的
                back_turn = r
            elif the_first_direction == r
                back_turn = l
            stop_num = 2 #因为跳过了第一个路口,所以还是2
            turn_num = 999 #弃之不用,5678用
            all_directions = [the_first_direction,back_turn,f]#这是主车，要走到最后，最后一个目前随便写的
            for direction in all_directions: 
                track_line(stop_num,turn_num,num,the_first_direction) #the_first_direction实际是l或者r，要传给从车,让从车知道怎么走
                turn_count += 1  # 每次转弯后增加计数
                print('Turning number:', turn_count, 'Direction:', direction)
                turn_at_intersection(direction)
            end_turn() #也许要换成一个走出去的函数
            '''
                我想是不是可以直接转过第一个弯后runrun(超级长时间,超级大速度)直接走出去,不需要再识别了,但还没有改动,就把f删了,end_turn()换了就好
            '''
        elif num == 5:
            all_directions = [f,f,r,f]#最后一个随便写, 实际在track_line()里面停了,后面不会用了 
            
        elif num == 6:
            all_directions = [f,f,l,f]#最后一个随便写, 实际在track_line()里面停了,后面不会用了 
            
        elif num == 7:
            all_directions = [f,f,l,f]#最后一个随便写, 实际在track_line()里面停了,后面不会用了 
            
        elif num == 8:
            all_directions = [f,f,r,f]#最后一个随便写, 实际在track_line()里面停了,后面不会用了 
            stop_num = 5 #在哪条线上停
            turn_num = 3 #在哪条线上掉头
            if(run_flag == 0):   
                car.Car_Run(50, 50)
                time.sleep(0.5)
                run_flag = 1
    

        

except KeyboardInterrupt:
    pass

finally:
    car.Car_Run(100,100)
    time.sleep(0.1)
    car.Car_Stop()
    del car
    print("Ending")
    GPIO.cleanup()
