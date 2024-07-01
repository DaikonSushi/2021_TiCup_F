import cv2
import numpy as np

def preprocess_image(frame):
    height, width = frame.shape[:2]
    cropped_frame = frame[height//2:, width//4:width*3//4]
    # 转换为灰度图像
    gray = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
    # 高斯模糊
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # 二值化
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary, cropped_frame

def find_contours(binary_image):
    # 查找轮廓
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def recognize_digits(binary_image, contours, templates, min_area):
    recognized_digits = []
    for contour in contours:
        # 检查轮廓面积
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        
        # 获得轮廓的边界框
        x, y, w, h = cv2.boundingRect(contour)
        # 提取轮廓内的区域
        digit_roi = binary_image[y:y+h, x:x+w]
        # 调整大小与模板匹配
        digit_roi = cv2.resize(digit_roi, (20, 20))
        
        scores = []
        for template in templates:
            # 比较模板与ROI
            result = cv2.matchTemplate(digit_roi, template, cv2.TM_CCOEFF_NORMED)
            _, score, _, _ = cv2.minMaxLoc(result)
            scores.append(score)
        
        # 选择匹配得分最高的模板
        recognized_digit_index = np.argmax(scores)
        # 转换索引为实际的数字
        recognized_digit = recognized_digit_index + 3  # 这里+3是因为模板是从3开始的
        recognized_digits.append((recognized_digit, (x, y, w, h)))
    return recognized_digits

def load_templates():
    templates = []
    for i in range(3, 8):
        template = cv2.imread(f'{i}.png', cv2.IMREAD_GRAYSCALE)
        _, template = cv2.threshold(template, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        template = cv2.resize(template, (20, 20))
        templates.append(template)
    return templates

def main():
    # 加载数字模板
    templates = load_templates()

    # 打开视频捕获
    cap = cv2.VideoCapture(1)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 预处理图像
        binary_image, cropped_frame = preprocess_image(frame)
        
        # 查找轮廓
        contours = find_contours(binary_image)
        
        # 识别数字（只对面积大于1000的区域）
        min_area = 1000
        recognized_digits = recognize_digits(binary_image, contours, templates, min_area)

        # 在裁剪后的图像上绘制识别结果
        for digit, (x, y, w, h) in recognized_digits:
            cv2.rectangle(cropped_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(cropped_frame, str(digit), (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # 显示结果
        cv2.imshow('Digit Recognition', cropped_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
