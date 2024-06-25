import cv2
import numpy as np
from sklearn import datasets, svm, metrics

# 加载数字数据集
digits = datasets.load_digits()
n_samples = len(digits.images)
data = digits.images.reshape((n_samples, -1))

# 创建SVM分类器
classifier = svm.SVC(gamma=0.001)

# 使用前半部分数据进行训练
classifier.fit(data[:n_samples // 2], digits.target[:n_samples // 2])

# 读取图像
img = cv2.imread('digits.png')

# 转换为灰度图像
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 二值化处理
ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

# 找到所有的轮廓
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for cnt in contours:
    # 获取边界框
    x, y, w, h = cv2.boundingRect(cnt)

    # 提取边界框内的图像
    roi = thresh[y:y+h, x:x+w]

    # 调整图像大小
    roi = cv2.resize(roi, (8, 8), interpolation=cv2.INTER_AREA)
    roi = roi.reshape((1, -1))

    # 预测
    digit = classifier.predict(roi)[0]
    print('识别的数字是：', digit)

    # 在原图像上绘制边界框和预测结果
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(img, str(digit), (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

# 显示图像
cv2.imshow('img', img)
cv2.waitKey(0)
cv2.destroyAllWindows()