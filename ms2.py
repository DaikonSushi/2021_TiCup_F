import cv2
import numpy as np
from tensorflow.keras.models import load_model

# 加载改进后的模型
model = load_model('strong_digit_recognition_model.h5')
i=0
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

# 打开摄像头
cap = cv2.VideoCapture(0)

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
            print("here")
            digit = 1

    if digit == 0 and contour is not None:
        digit = 4

    # 在帧上显示预测结果
    cv2.putText(frame, f'Digit: {digit}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # 如果检测到方框，圈起来
    if bbox is not None:
        x, y, w, h = bbox
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # 显示带预测结果的帧
    #cv2.imshow('Digit Recognition', frame)
    
    # 显示识别的图像
    #if digit_img is not None:
    #    cv2.imshow('Recognized Digit', digit_img)
    
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
    if i>50:
        counts = [one, two, three, four, five, six, seven, eight]
        print(counts)
        max_count = max(counts)
        max_digit = counts.index(max_count) + 1  # 加1是因为列表索引从0开始，而数字从1开始
        one,two,three,four,five,six,seven,eight,i = 0,0,0,0,0,0,0,0,0
        return max_digit
        



result = reco()
print(result)
# 释放摄像头并关闭所有窗口
cap.release()
cv2.destroyAllWindows()
