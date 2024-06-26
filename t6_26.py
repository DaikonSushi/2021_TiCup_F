import RPi.GPIO as GPIO
import time
import YB_Pcb_Car  # 导入Yahboom专门库文件
import cv2
import ipywidgets.widgets as widgets
import threading
import numpy as np
import enum
import ms2 #用于识别数字，包含tensorflow库


car = YB_Pcb_Car.YB_Pcb_Car()
time_turning = 1.05
time_going = 0.2
speed_spin = 160 #转弯速度
speed_go = 40 #巡线直行速度


# 循迹红外引脚定义
Tracking_Right1 = 11  # X1A  右边第一个传感器
Tracking_Right2 = 7  # X2A  右边第二个传感器
Tracking_Left1 = 13  # X1B 左边第一个传感器
Tracking_Left2 = 15  # X2B 左边第二个传感器

def setup_gpio():
    # 设置GPIO口为BCM编码方式
    GPIO.setmode(GPIO.BOARD)

    # 忽略警告信息
    GPIO.setwarnings(False)

    GPIO.setup(Tracking_Left1, GPIO.IN)
    GPIO.setup(Tracking_Left2, GPIO.IN)
    GPIO.setup(Tracking_Right1, GPIO.IN)
    GPIO.setup(Tracking_Right2, GPIO.IN)

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
def runrun(runruntime,stop__num):
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
            car.Car_Run(30, 30)
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
def track_line(stop_num):
    global turn_count,red_real, red_fake, blue_real, blue_fake
    while True:
        TrackSensorLeftValue1 = GPIO.input(Tracking_Left1)
        TrackSensorLeftValue2 = GPIO.input(Tracking_Left2)
        TrackSensorRightValue1 = GPIO.input(Tracking_Right1)
        TrackSensorRightValue2 = GPIO.input(Tracking_Right2)
        #0xxx或xxx0退出循迹
        # 停止条件
        if turn_count == stop_num:
            runrun(1.1,stop_num)
            runalittle()
            car.Car_Run(40,40)
            time.sleep(0.01)
            car.Car_Stop()
            time.sleep(2.5)
            turn_180()
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
    l=0,0
    r=1,1
    f=2,2
    while True : #这是一个死循环，会每次回到起点，打开摄像头，识别代码，按照代码规划路径，走到最后结束
        cap = cv2.VideoCapture(0) #打开摄像头
        num = ms2.reco() #识别代码
        print(num)
        cap.release()# 释放摄像头
        #cv2.destroyAllWindows()
        turn_count = 1    # 用于跟踪转弯次数
        # 路线规划，走进去、掉头、走出来，与期末时期逻辑相同
        if(num==1):
            all_directions = [l,r] 
            stop_num = 2
        elif(num==2):
            all_directions = [r,l]   
            stop_num = 2
        elif(num==3):
            all_directions = [f,l,r,f]
            stop_num = 3
        elif(num==4):
            all_directions = [f,r,l,f]
            stop_num =3
        elif(num==5):
            all_directions = [f,f,l,l,r,r,f,f]
            stop_num = 5
        elif(num==6):
            all_directions = [f,f,l,r,l,r,f,f]
            stop_num = 5
        elif(num==7):
            all_directions = [f,f,r,r,l,l,f,f]
            stop_num = 5
        elif(num==8):
            all_directions = [f,f,r,l,r,l,f,f]
            stop_num = 5
            
        for direction in all_directions: #按照规划的路径开走，走到最后退出进入"end_turn()"函数
            track_line(stop_num)
            turn_count += 1  # 每次转弯后增加计数
            print('Turning number:', turn_count, 'Direction:', direction)
            turn_at_intersection(direction)
        end_turn() #end_turn()函数，走到最后一段直线，转180度，结束
        

except KeyboardInterrupt:
    pass

finally:
    car.Car_Stop()
    del car
    print("Ending")
    GPIO.cleanup()
