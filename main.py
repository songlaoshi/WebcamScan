# !/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import requests
import cv2
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow
from Webcam import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QButtonGroup, QLabel, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage, QPen,QBrush, QPolygon, QPolygonF, QColor, QPainter, QFont
from PyQt5.QtCore import Qt, QTimer, QPoint, QPointF, QRect
import numpy as np
# 设置全局变量
WIDTH_ORI , HEIGHT_ORI= 1296, 960 
WIDTH, HEIGHT =450,608 #608, 450

class My_Application(QMainWindow):
    def __init__(self, ip_address="192.168.0.100", save_path='./'):
        super().__init__()
        self.ip_address = ip_address
        self.save_path = save_path
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # 创建按钮组
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.ui.checkBox)
        self.button_group.addButton(self.ui.checkBox_2)

        # 连接按钮的点击事件到槽函数
        self.ui.pushButton.clicked.connect(self.start_image_capture) 
    
    def start_image_capture(self):
        # 获取用户输入的IP地址和保存路径
        self.ip_address = self.ui.lineEdit.text()
        self.save_path = self.ui.lineEdit_2.text()
        # 获取选择的相机类型
        selected_button = self.button_group.checkedButton()
        camera_type = ""
        if selected_button == self.ui.checkBox:
            self.camera_type = 'RGB'
        elif selected_button == self.ui.checkBox_2:
            self.camera_type = 'RGB+IR'
        # 在输出日志部分显示相应的日志
        log_message = f"相机IP地址:{self.ip_address}\n数据保存路径:{self.save_path}\n相机类型:{self.camera_type}\n开始获取图像......"
        self.ui.textBrowser.append(log_message)
        ################# show image ####################
        ##### phenocam
        self.image_url = f"http://{self.ip_address}//netcam.jpg"
        self.ui.label_image.setScaledContents(True)
        self.ui.label_image.setAlignment(Qt.AlignCenter)
        # self.time_points = []  # 用于保存时间点
        # self.roi = np.array([[135, 505],[295, 495],[298, 555],[115, 581]]) # roi range
        # 计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_image)
        self.timer.start(60000)  # 设置定时器间隔为60秒

        self.show_image()  # 首次加载图片

    def roiCorTransf(self, roi):
        roi_points, layer_points = [], []
        for i in range(len(roi)):
            roi_points.append(QPoint(roi[i,0],roi[i,1]))
            layer_points.append(QPoint(int(roi[i,0]/WIDTH_ORI*WIDTH),int(roi[i,1]/HEIGHT_ORI*HEIGHT)))
        return roi_points, layer_points
    
    def show_image(self):
        if self.camera_type == "RGB":
            try:
                response = requests.get(self.image_url)
                if response.status_code == 200:
                    # 获取当前时间
                    strtime, current_time= self.getstrTime()
                    # 获取图像
                    image = QPixmap()
                    image.loadFromData(response.content)
                    # 绘制原始图像
                    scaled_image = image.scaled(WIDTH, HEIGHT,Qt.KeepAspectRatio, Qt.SmoothTransformation) #
                    self.ui.label_image.setPixmap(scaled_image)
                    # 保存图像
                    current_time = datetime.datetime.now()
                    #检查是否在每天6点到19点之间
                    if 0<= current_time.hour<24:
                        # 检查是否是整点
                        if current_time.minute == 40:
                            # 使用OpenCV加载图像并转换为NumPy数组
                            numpy_image = cv2.imdecode(np.frombuffer(response.content, dtype=np.uint8), -1)
                            # 保存图像
                            self.save_hourly_image_RGB(numpy_image, strtime)
                            # 显示日志
                            log_message = strtime+ ", 图像获取成功。"
                            self.ui.textBrowser.append(log_message)
                        else:
                            # 显示日志
                            log_message = strtime+ ", 显示实时图像成功。"
                            self.ui.textBrowser.append(log_message)
                else:
                    print("Failed to fetch image. Status code:", response.status_code)
                    # 显示日志
                    log_message = "获取图像失败, 状态码:{response.status_code}"
                    self.ui.textBrowser.append(log_message)
            except requests.exceptions.RequestException as e:
                print("Error:", e)
        elif self.camera_type == "RGB+IR":
            try:
                response = requests.get(self.image_url)
                if response.status_code == 200:
                    # 获取当前时间
                    strtime, current_time= self.getstrTime()
                    # 获取图像
                    image = QPixmap()
                    image.loadFromData(response.content)
                    # 绘制原始图像
                    scaled_image = image.scaled(WIDTH, HEIGHT,Qt.KeepAspectRatio, Qt.SmoothTransformation) #
                    self.ui.label_image.setPixmap(scaled_image)
                    # 保存图像
                    current_time = datetime.datetime.now()
                    #检查是否在每天6点到19点之间
                    if 7<= current_time.hour<24:
                        # 检查是否是整点
                        if current_time.minute > 0:
                            # print('a')
                            # 使用OpenCV加载图像并转换为NumPy数组
                            numpy_image = cv2.imdecode(np.frombuffer(response.content, dtype=np.uint8), -1)
                            # 判断当前图像是RGB通道还是IR通道
                            flag = self.isRGBorIR(numpy_image)
                            # print(flag)
                            # 保存图像
                            # 显示日志
                            log_message = strtime+ ", 在观测时间内. 开始获取图像..."
                            self.ui.textBrowser.append(log_message)

                            self.save_hourly_image(numpy_image, flag, strtime)
                            # self.save_hourly_image(self, image)
                            # 显示日志
                            log_message = strtime+ ", 图像获取成功。"
                            self.ui.textBrowser.append(log_message)
                        else:
                            # 显示日志
                            log_message = strtime+ ", 显示实时图像成功。"
                            self.ui.textBrowser.append(log_message)
                else:
                    print("Failed to fetch image. Status code:", response.status_code)
                    # 显示日志
                    log_message = "获取图像失败, 状态码:{response.status_code}"
                    self.ui.textBrowser.append(log_message)
            except requests.exceptions.RequestException as e:
                print("Error:", e)

    # def save_hourly_image(self, image):
    #     current_time = datetime.datetime.now()
    #     #检查是否在每天6点到19点之间
    #     if 7<= current_time.hour<19:
    #         # 检查是否是整点
    #         if current_time.minute == 0:
    #             save_path = self.save_path
    #             file_name = f"{self.save_path}/image_{current_time.strftime('%Y%m%d_%H%M%S')}.jpg"
    #             image.save(file_name)


    def getstrTime(self):
        current_time = datetime.datetime.now()
        stime = current_time.strftime("%Y-%m-%d-%H-%M-%S")
        # time_now = (datetime_now.strftime('%H:%M:%S')).split(":")
        # doy_h = (int(time_now[0])+int(time_now[1])/60+int(time_now[2])/3600)/24
        # doy_d = datetime_now.timetuple().tm_yday
        return stime, current_time#doy_d+doy_h
    
    def isRGBorIR(self, numpy_image):
        r,g,b = numpy_image[:,:,0],numpy_image[:,:,1],numpy_image[:,:,2]
        totalnum = np.sum(r>0)
        if (np.sum(r==g)/totalnum>0.95): # 左上角水印导致r,g,b不能完全相等
            return 1  # 用1表示IR通道
        else: 
            return 0  # 用0表示RGB通道
    
    def save_hourly_image_RGB(self, numpy_image, strtime):
        # 保存当前图像为RGB图像
        savename = self.save_path + '\\' + strtime + '_RGB.jpeg'
        cv2.imwrite(savename, numpy_image)
            

    def save_hourly_image(self, numpy_image, flag, strtime):
        if flag==0: # 如果当前是RGB通道
            # 先保存当前图像为RGB图像
            savename = self.save_path + '\\' + strtime + '_RGB.jpeg'
            cv2.imwrite(savename, numpy_image)
            # 显示日志
            log_message = strtime+ ", RGB图像获取成功。"
            self.ui.textBrowser.append(log_message)
            # 建立循环，寻找后面时刻第一个IR图像
            while True:
                # 读取下一时刻的图像
                response = requests.get(self.image_url)
                if response.status_code == 200:
                    # 获取当前时间
                    strtime, _ = self.getstrTime()
                    # 显示日志
                    log_message = strtime+ ", 寻找IR图像......"
                    self.ui.textBrowser.append(log_message)
                    # 使用OpenCV加载图像并转换为NumPy数组
                    numpy_image2 = cv2.imdecode(np.frombuffer(response.content, dtype=np.uint8), -1)
                    # 判断当前图像是RGB通道还是IR通道
                    flag = self.isRGBorIR(numpy_image2)
                    if flag == 1: # 如果是IR图像
                        # 保存IR图像
                        savename = self.save_path + '\\' + strtime + '_IR.jpeg'
                        cv2.imwrite(savename, numpy_image2)
                        # self.saveImage(numpy_image, flag, strtime)
                        # 保存NDVI图像
                        savename = self.save_path + '\\' + strtime + '_NDVI.jpeg'
                        ndvi = float(numpy_image2[:,:,0]-numpy_image[:,:,0])/(numpy_image2[:,:,0]+numpy_image[:,:,0])
                        cv2.imwrite(savename, ndvi)
                        # 显示日志
                        log_message = strtime+ ", 获取IR和NDVI图像成功。"
                        self.ui.textBrowser.append(log_message)
                        # 退出循环
                        break
                    else: # 如果是RGB图像，继续循环
                        continue
                else:
                    print("Failed to fetch image. Status code:", response.status_code)
        else: # 当前为IR通道
            # 先保存当前图像为IR图像
            savename = self.save_path + '\\' + strtime + '_IR.jpeg'
            cv2.imwrite(savename, numpy_image)
            # 显示日志
            log_message = strtime+ ", IR图像获取成功。"
            self.ui.textBrowser.append(log_message)
            # 建立循环，寻找后面时刻第一个RGB图像
            while True:
                # 读取下一时刻的图像
                response = requests.get(self.image_url)
                if response.status_code == 200:
                    # 获取当前时间
                    strtime, _  = self.getstrTime()
                    # 显示日志
                    log_message = strtime+ ", 寻找IR图像......"
                    self.ui.textBrowser.append(log_message)
                    # print(strtime, ' trying....')
                    # 使用OpenCV加载图像并转换为NumPy数组
                    numpy_image2 = cv2.imdecode(np.frombuffer(response.content, dtype=np.uint8), -1)
                    # 判断当前图像是RGB通道还是IR通道
                    flag = self.isRGBorIR(numpy_image2)
                    if flag == 0: # 如果是RGB图像
                        # 保存图像
                        savename = self.save_path + '\\' + strtime + '_RGB.jpeg'
                        cv2.imwrite(savename, numpy_image2)
                        # 保存NDVI图像
                        savename = self.save_path + '\\' + strtime + '_NDVI.jpeg'
                        ndvi = float(numpy_image[:,:,0]-numpy_image2[:,:,0])/(numpy_image2[:,:,0]+numpy_image[:,:,0])
                        cv2.imwrite(savename, ndvi)
                        # self.saveImage(numpy_image, flag, strtime)
                        # 退出循环
                        # 显示日志
                        log_message = strtime+ ", 获取RGB和NDVI图像成功。"
                        self.ui.textBrowser.append(log_message)
                        break
                    else: # 如果是IR图像，继续循环
                        continue
                else:
                    print("Failed to fetch image. Status code:", response.status_code)

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     MainWindow = QMainWindow()
#     ui = Webcam.Ui_MainWindow()
#     ui.setupUi(MainWindow)
#     MainWindow.show()
#     sys.exit(app.exec_())
def main():
    app = QApplication(sys.argv)
    my_window = My_Application()
    my_window.setWindowTitle("WebimageScan")
    my_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()