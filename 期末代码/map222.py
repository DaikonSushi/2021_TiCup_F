import RPi.GPIO as GPIO
import time
import YB_Pcb_Car  # 导入Yahboom专门库文件

import cv2
import ipywidgets.widgets as widgets
import threading
import time
import numpy as np
import enum

image_widget = widgets.Image(format='jpeg', width=600, height=500)  #设置摄像头显示组件大小
def bgr8_to_jpeg(value, quality=75):
    return bytes(cv2.imencode('.jpg', value)[1])

car = YB_Pcb_Car.YB_Pcb_Car()
time_turning = 1.05
time_going = 0.2
speed_spin = 160 #转弯速度
speed_turn_180 = 63 #180度转弯速度
speed_go = 30 #巡线直行速度
crash_speed_long = 140 #撞宝藏的速度
crash_time_long = 0.5 #撞宝藏的时间
crash_speed = 100 #撞宝藏的速度
crash_time = 0.5 #撞宝藏的时间
back_speed = 90 #撞宝藏后退的速度
back_time = 0.4 #撞宝藏后退的时间
map_num=2

# 循迹红外引脚定义
Tracking_Right1 = 11  # X1A  右边第一个传感器
Tracking_Right2 = 7  # X2A  右边第二个传感器
Tracking_Left1 = 13  # X1B 左边第一个传感器
Tracking_Left2 = 15  # X2B 左边第二个传感器
red_lower = np.array([0, 43, 46])
red_upper = np.array([10, 255, 255])
cyan_lower = np.array([80, 100, 100])
cyan_upper = np.array([100, 255, 255])
yellow_lower = np.array([17,105,88])
yellow_upper = np.array([63,255,255])
blue_lower = np.array([89, 82, 22])
blue_upper = np.array([150, 255, 255])

red_real = 0
red_fake = 0
blue_real = 0
blue_fake = 0

image_widget = widgets.Image(format='jpeg', width=600, height=500)  #设置摄像头显示组件大小

def Color_Recongnize():
    image = cv2.VideoCapture(0)#打开摄像头
    print("3")
    # width=1280
    # height=960
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH,width)#设置图像宽度
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT,height)#设置图像高度

    image.set(3,600)       
    image.set(4,500)
    image.set(5, 30)  #设置帧率
    image.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))

    image.set(cv2.CAP_PROP_BRIGHTNESS, 62)  # 设置亮度 -64 - 64  0.0
    image.set(cv2.CAP_PROP_CONTRAST, 63)  # 设置对比度 -64 - 64  2.0
    image.set(cv2.CAP_PROP_EXPOSURE, 4800)  # 设置曝光值 1.0 - 5000  156.0
    global red_real, red_fake, blue_real, blue_fake

    i=0
    ret, frame = image.read()  # 确保在循环开始前先读取一帧图像
    while i<30:
        image_widget.value = bgr8_to_jpeg(frame)
        ret, frame = image.read()
        frame = cv2.resize(frame, (320, 240))
        frame_ = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 颜色分割a
        mask_red = cv2.inRange(hsv, red_lower, red_upper)
        mask_cyan = cv2.inRange(hsv, cyan_lower, cyan_upper)
        mask_yellow = cv2.inRange(hsv, yellow_lower, yellow_upper)
        mask_blue = cv2.inRange(hsv, blue_lower, blue_upper)

        # 寻找轮廓
        contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_cyan, _ = cv2.findContours(mask_cyan, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_yellow, _ = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        i+=1

        # 定义结果字符串
        
        # 判断是否为宝藏或伪宝藏
        if len(contours_red) > 0 and len(contours_yellow) > 0:
            red_fake+=1
        elif len(contours_red) > 0 :
            red_real+=1
        elif len(contours_blue) > 0 and len(contours_yellow) > 0:
            blue_real+=1
        elif len(contours_blue) > 0 :
            blue_fake+=1
    
    image.release()  
        # 绘制结果文字
    print(red_real)
    if(max(red_real, red_fake, blue_real, blue_fake)==red_real):
        print("red_real")
        return "red_real"
    elif(max(red_real, red_fake, blue_real, blue_fake)==red_fake):
        print("red_fake")
        return "red_fake"
    elif(max(red_real, red_fake, blue_real, blue_fake)==blue_real):
        print("blue_real")
        return "blue_real"
    else:
        print("blue_fake")
        return "blue_fake"
    
def setup_gpio():
    # 设置GPIO口为BCM编码方式
    GPIO.setmode(GPIO.BOARD)

    # 忽略警告信息
    GPIO.setwarnings(False)

    GPIO.setup(Tracking_Left1, GPIO.IN)
    GPIO.setup(Tracking_Left2, GPIO.IN)
    GPIO.setup(Tracking_Right1, GPIO.IN)
    GPIO.setup(Tracking_Right2, GPIO.IN)
def turn_180():
    start_time = time.time()
    while True:
        car.Car_Turn_180_(70)
        if (time.time() - start_time >= 1):   
            break
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        car.Car_Turn_180_(70)
        #0xxx或xxx0退出循迹
        if (TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False):
            car.Car_Run(30,30)
            time.sleep(0.01)
            break
    pass
def crash(treassure,speed): #冲撞函数
    if (treassure == 'blue_real'):
        if(speed==1): 
            car.Car_Run(crash_speed, crash_speed)
            time.sleep(crash_time)
            car.Car_Back(back_speed, back_speed)
            time.sleep(back_time)
        else:
            car.Car_Run(crash_speed_long, crash_speed_long)
            time.sleep(crash_time_long)
            car.Car_Back(back_speed, back_speed)
            time.sleep(back_time)
        pass
    else:
        runrun(0.4)
        pass
def crash1(treassure,speed): #冲撞函数
    if (treassure == 'blue_real'):
        if(speed==1): 
            car.Car_Run(120, 120)
            time.sleep(crash_time)
            car.Car_Back(back_speed, back_speed)
            time.sleep(back_time)
        else:
            car.Car_Run(120, 120)
            time.sleep(crash_time_long)
            car.Car_Back(back_speed, back_speed)
            time.sleep(back_time)
        pass
    else:
        runrun(0.4)
        pass



def runrun(runruntime):
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
            car.Car_Run(45, 45)
        # 假路口判断
        #1011   车偏右
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
            car.Car_Left(0, 90)
        #1101   车偏左
        elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
            car.Car_Right(90, 0)
        elif TrackSensorLeftValue1 == True :
            car.Car_Right(100, 0)
        elif TrackSensorRightValue1 == True :
            car.Car_Left(0, 100)
def backback(backbacktime,speed):
    start_time = time.time()
    print('start')
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        #0xxx或xxx0退出循迹
        if (time.time() - start_time >= backbacktime):
            runrun(0.3)
            break
        #1001 直行
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
            car.Car_Back(speed,speed)
        # 假路口判断
        #1011   车偏右
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
            car.Car_Right(35, 0)
        #1101   车偏左
        elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
            car.Car_Left(0, 35)


# 循迹部分
def track_line():
    global turn_count,red_real, red_fake, blue_real, blue_fake
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        #0xxx或xxx0退出循迹

        '''
        elif turn_count == 0 and (TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False):
            car.Car_Run(70, 70)
        elif turn_count == 6 and (TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False):
            car.Car_Run(30, 30)
        elif turn_count == 8 and (TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False):
            car.Car_Run(30, 30)
        elif turn_count == 9 and (TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False):
            car.Car_Run(30, 30)
        elif turn_count == 10 and (TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False):
            car.Car_Run(130, 130)
        elif turn_count == 11 and (TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False):
            car.Car_Run(40, 40)

        '''
        # 停止条件
        if turn_count == 14 or turn_count == 34 or turn_count == 40  or turn_count == 60:
            runrun(1.1)
            time.sleep(0.01)
            car.Car_Stop()
            time.sleep(1)
            crash(Color_Recongnize(),2)
            red_real = 0
            red_fake = 0
            blue_real = 0
            blue_fake = 0
            turn_180()
            turn_count += 1
            continue
        elif turn_count == 22 or turn_count == 29 or turn_count == 52 or turn_count == 45:
            backback(0.5,50)
            time.sleep(0.01)
            car.Car_Stop()
            time.sleep(1)
            crash1(Color_Recongnize(),2)
            red_real = 0
            red_fake = 0
            blue_real = 0
            blue_fake = 0
            
            turn_180()
            backback(0.3,40)
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
        elif direction == 3:
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
            if current_time2 - start_time >= 0.8:
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

        elif direction == 4:   #最后冲刺
            #x00x直行
            if TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
                car.Car_Run(100, 100)
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                car.Car_Left(0, 70)
            elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                car.Car_Right(70, 0)

            current_time3 = time.time()
            if current_time3 - start_time >= 5:
                break
try:
    setup_gpio()
    l,bl=0,0
    r,br=1,1
    f,bf=2,2
    if(map_num==1):
        all_directions = [l,l,r,r,l,r,f,r,bl,l,l,r,r,br,l,l,r,r,l,f,f,bl,r,f,r,r,l,r,l,r,l,bf,l,f,f,l,r,f,bl,r,l,r,l,r,l,l,f,bl,r,f,f,r,bf,l,l,r,br,l,l,l,r,f,l,f,l,r,l,l,r,r,f,f,f] #map1
    elif(map_num==2):
        all_directions = [l,l,r,r,l,r,f,r,f,l,r,r,br,l,l,r,r,l,f,bl,r,r,r,l,f,br,l,r,r,bl,l,l,r,f,br,r,l,l,br,l,f,r,l,l,bl,r,f,r,l,l,r,br,l,l,l,r,f,l,f,l,r,l,l,r,r,f,f,f,f ]   #map2
    elif(map_num==3):
        all_directions = [l,l,r,r,l,r,f,r,f,l,r,r,br,l,l,r,r,l,f,bl,r,f,r,r,l,f,br,l,r,r,bl,l,l,f,f,r,r,f,f,r,r,l,r,r,br,l,r,r,bl,r,l,r,r,l,l,f,bl,r,f,f,r,l,l,r,br,l,l,l,r,f,l,f,l,r,l,l,r,r]#map3
    #all_directions = [0,0,1,2,1,1,0,0,1,0]#[0,0,1,1,0,1,2,1,2,0,1,1,1,0,0,0,0,1,0]#2-3 #[0,0,1,1,0,1,0,1,0,1,2,0,1,0,1,0,0,1,3,4]
    turn_count = 1  # 用于跟踪转弯次数

    for direction in all_directions:
        track_line()
        turn_count += 1  # 每次转弯后增加计数
        print('Turning number:', turn_count, 'Direction:', direction)
        turn_at_intersection(direction)

except KeyboardInterrupt:
    pass

finally:
    car.Car_Stop()
    del car
    print("Ending")
    GPIO.cleanup()
