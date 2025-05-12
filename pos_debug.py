# -*- coding: utf-8 -*-

# Created by: Raf

# 这个文件用来辅助调整截图区域坐标。运行游戏，全屏截图，放上路径，就可以查看截图区域。

import cv2

# Modify the region parameters and the image path
capture_pos = [(324, 750, 1131, 75),    # 玩家区域
               (300, 330, 380, 160),    # 玩家上家区域
               (1250, 330, 380, 160),   # 玩家下家区域
               (130, 157, 90, 90),   # 地主标志区域(玩家上家)
               (32, 675, 90, 90),    # 地主标志区域(玩家)
               (1409, 157, 90, 90),    # 地主标志区域(玩家下家)
               (850, 68, 220, 110)      # 地主底牌区域 # 修改完成
               ]
# (左上角x, 左上角y, 宽度, 高度)
# img_path = r"H:\git_repos\DouZero_For_HappyDouDiZhu\screenshots\2025-05-09 16-23-24.mkv_20250509_165039.438.png" #'C:/Users/Raf/Desktop/screenshot/1.png'
# img_path = r"H:\git_repos\DouZero_For_HappyDouDiZhu\screenshots\2025-05-09 16-23-24.mkv_20250509_170725.720.png"
# img_path = r"H:\git_repos\DouZero_For_HappyDouDiZhu\screenshots\2025-05-09 16-23-24.mkv_20250509_170801.113.png"
img_path = r"D:\22844\Pictures\Screenshots\屏幕截图 2025-05-09 232034.png"
colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0), (255, 0, 255), (0, 255, 255), (255, 255, 255)]

img = cv2.imread(img_path)
for pos, color in zip(capture_pos, colors):
    img = cv2.rectangle(img, pos[0:2], (pos[0] + pos[2], pos[1] + pos[3]), color, 1)
# cv2.namedWindow("test", 0)
cv2.imshow("test", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
