import cv2
import numpy as np
import YB_Pcb_Car
import RPi.GPIO as GPIO
import time
import multiprocessing
import ipywidgets as widgets
from IPython.display import display, Image

time_turning = 2
time_going = 0.2
speed_spin = 160 #转弯速度
speed_go = 40 #巡线直行速度

car = YB_Pcb_Car.YB_Pcb_Car()
speed_go = 80  # 巡线直行速度
correct_speed = 70 # 巡线校正速度

turn_run_speed = 80       # 转弯时直行速度
turn_run_time = 0.5 # 转弯前直行时间 

turn_speed = 120    # 转弯速度
turn_time = 0.11    # 转弯时间

turn_runding_speed = 80
turn_runding_time = 0.35
turn_flag = 0

Tracking_Right1 = 11  # X1A  右边第一个传感器
Tracking_Right2 = 7  # X2A  右边第二个传感器
Tracking_Left1 = 13  # X1B 左边第一个传感器
Tracking_Left2 = 15  # X2B 左边第二个传感器

def bgr8_to_jpeg(value, quality=75):
    return bytes(cv2.imencode('.jpg', value)[1])

# 显示摄像头组件
image_widget = widgets.Image(format='jpeg', width=320, height=240)
display(image_widget)

def spin(dir,turn_module):
    start_time = time.time()
    while True:
        if(turn_module == 'lr'):
            if (time.time() - start_time > turn_run_time):
                break   
            car.Car_Run(turn_run_speed, turn_run_speed)
        elif(turn_module == 'ding'):
            if (time.time() - start_time > turn_runding_time):
                break   
            car.Car_Run(turn_runding_speed, turn_runding_speed)
    start_time = time.time()
    while True:
            if (time.time() - start_time > turn_time):
                break
            if(dir == 0):
                car.Car_Left(70, turn_speed)
            elif(dir == 1):
                car.Car_Right(turn_speed, 70)
            elif(dir == 2):
                car.Car_Run(60, 60)       
def setup_gpio():
    # 设置GPIO口为BCM编码方式
    GPIO.setmode(GPIO.BOARD)

    # 忽略警告信息
    GPIO.setwarnings(False)

    GPIO.setup(Tracking_Left1, GPIO.IN)
    GPIO.setup(Tracking_Left2, GPIO.IN)
    GPIO.setup(Tracking_Right1, GPIO.IN)
    GPIO.setup(Tracking_Right2, GPIO.IN)

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
                car.Car_Run(40, 40)
            # 101x   车偏右
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                car.Car_Left(0, correct_speed)
            # 110x   车偏左
            elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                car.Car_Right(correct_speed, 0)

            current_time1 = time.time()
            if current_time1 - start_time >= time_turning:
                break
        elif direction == 1:
            #xxx0
            if TrackSensorRightValue2 == False:
                car.Car_Spin_Right(speed_spin, 0)
            #x001   非右转
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
                car.Car_Run(40, 40)
            #x011   车偏右
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                car.Car_Left(0, correct_speed)
            #x101   车偏左
            elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                car.Car_Right(correct_speed, 0)

            current_time2 = time.time()
            if current_time2 - start_time >= time_turning:
                break
        elif direction == 2:
            #x00x直行
            if TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
                car.Car_Run(70, 70)
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                car.Car_Left(0, correct_speed)
            elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                car.Car_Right(correct_speed, 0)

            current_time3 = time.time()
            if current_time3 - start_time >= time_going:
                break
        
#转头函数，先开转，速度为100，转0.8秒，肯定转不完，再以50的速度转，直到两个传感器都在黑线上，能保证转到位
def turn_180():
    start_time = time.time()
    while True:
        car.Car_Turn_180_(100)
        if (time.time() - start_time >= 0.8):   
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
            car.Car_Left(0, 90)
        #1101   车偏左
        elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
            car.Car_Right(90, 0)
        elif TrackSensorLeftValue1 == True :
            car.Car_Right(100, 0)
        elif TrackSensorRightValue1 == True :
            car.Car_Left(0, 100)

# 循迹部分，停车功能写在这里
def track_line(stop_num):
    global turn_count,turn_flag
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        if turn_count == stop_num: 
            runrun(1.1,30)
            runalittle()
            car.Car_Run(40,40)
            time.sleep(0.01)
            car.Car_Stop()
            time.sleep(2.5)
            turn_180()
            turn_count += 1
            continue    
        else:
            ret, frame = cap.read()
            if not ret:
                break
            # 将BGR图像转换为HSV颜色空间
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # 二值化处理
            _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
            # 寻找轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                # 找到最大轮廓
                c = max(contours, key=cv2.contourArea)
                # 计算轮廓的中心
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    # 在原图上标记中心
                    cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                    x, y, w, h = cv2.boundingRect(c)
                    # 获取图像中心
                    image_center = frame.shape[1] // 2
                    center_x = x + w // 2
                    frame_center = frame.shape[1] // 2
                    top_mid = (x + w // 2, y)
                    bottom_mid = (x + w // 2, y + h)
                    # 根据中心位置调整小车方向
                    image_widget.value = bgr8_to_jpeg(thresh)
            #0xxx或xxx0退出循迹
            # 停止条件
                if (w > frame.shape[1]*0.8  and h > frame.shape[0]*0.8) or (h < frame.shape[0]*0.8  and w > frame.shape[1]*0.8) or(h > frame.shape[0]*0.8 and center_x < frame_center - 150) or (h > frame.shape[0]*0.8 and center_x > frame_center + 150):
                    cap.release()
                    runrun(0.05,70)
                    turn_flag = 1
                    break
            #未退出说明假路口
                #1001 直行
                elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
                    car.Car_Run(speed_go, speed_go)
                # 假路口判断
                #1011   车偏右
                elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                    car.Car_Left(0, correct_speed)
                #1101   车偏左
                elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                    car.Car_Right(correct_speed, 0)
                else:
                    car.Car_Run(30, 30)



'''def line_recognition_and_correction(all_directions, turn_count):
    global turn_flag
    try:
        while True:
            TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
            TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
            TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
            TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
            ret, frame = cap.read()
            if not ret:
                break
            # 将BGR图像转换为HSV颜色空间
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # 二值化处理
            _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
            # 寻找轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                # 找到最大轮廓
                c = max(contours, key=cv2.contourArea)
                # 计算轮廓的中心
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    # 在原图上标记中心
                    cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                    x, y, w, h = cv2.boundingRect(c)
                    # 获取图像中心
                    image_center = frame.shape[1] // 2
                    center_x = x + w // 2
                    frame_center = frame.shape[1] // 2
                    top_mid = (x + w // 2, y)
                    bottom_mid = (x + w // 2, y + h)
                    # 根据中心位置调整小车方向
                    if w > frame.shape[1]*0.8  and h > frame.shape[0]*0.8:  # 如果轮廓宽度接近整个帧宽度，认为是十字路口
                        if(turn_flag == 0):
                            turn_at_intersection(all_directions[turn_count])
                            print("ten")
                        turn_flag = 1
                    elif (h < frame.shape[0]*0.8  and w > frame.shape[1]*0.8):  # 如果轮廓高度接近整个帧高度且宽度较大，认为是丁字路口
                        if(turn_flag == 0):
                            turn_at_intersection(all_directions[turn_count])
                            print("t")
                        turn_flag = 1
                    elif (h > frame.shape[0]*0.8 and center_x < frame_center - 150):
                        if(turn_flag == 0):
                            turn_at_intersection(all_directions[turn_count])
                            print("1")
                        turn_flag = 1
                    elif (h > frame.shape[0]*0.8 and center_x > frame_center + 150):
                        if(turn_flag == 0):
                            turn_at_intersection(all_directions[turn_count])
                            print("2")
                        turn_flag = 1
                        #1001 直行
                    elif center_x < frame_center - 150:  # 20 是一个阈值，可以调整
                        if(turn_flag == 0):
                            turn_at_intersection(all_directions[turn_count])
                            print("3")
                        turn_flag = 1
                    elif center_x > frame_center + 150:
                        if(turn_flag == 0):
                            turn_at_intersection(all_directions[turn_count])
                            print("4")
                        turn_flag = 1
                    else:
                        if TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
                            car.Car_Run(speed_go, speed_go)
                            turn_flag = 0
                        #1011   车偏右
                        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                            car.Car_Left(0, 90)
                        #1101   车偏左
                        elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                            car.Car_Right(90, 0)
                        else:
                            car.Car_Run(30, 30)
                        # 显示结果
                        image_widget.value = bgr8_to_jpeg(thresh)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
    except KeyboardInterrupt:
        pass

    cap.release()
    cv2.destroyAllWindows()'''


if __name__ == "__main__":
    try:
        turn_flag = 0
        setup_gpio()
        car.Ctrl_Servo(2, 160)  # 控制舵机 S2 旋转到 90 度
        car.Ctrl_Servo(1, 90)
        l = 0
        r = 1
        f = 2
        direction_queue = multiprocessing.Queue()
        all_directions = [l,r,r,l] 
        stop_num = 3
        turn_count = 0  # 用于跟踪转弯次数
        for direction in all_directions: #按照规划的路径开走，走到最后退出进入"end_turn()"函数
            cap = cv2.VideoCapture(0)
            track_line(stop_num)
            turn_count += 1  # 每次转弯后增加计数
            print('Turning number:', turn_count, 'Direction:', direction)
            turn_at_intersection(direction)
    except KeyboardInterrupt:
        pass
    finally:
        car.Car_Stop()
        del car
        print("Ending")
        cv2.destroyAllWindows()

