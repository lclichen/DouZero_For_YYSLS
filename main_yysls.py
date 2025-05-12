# -*- coding: utf-8 -*-

# Created by: Raf

import os
import sys
import time
import threading
import pyautogui
import datetime

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem, QInputDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QTime, QEventLoop
from MainWindowUI import Ui_Form

from douzero.env.game import GameEnv
from douzero.evaluation.deep_agent import DeepAgent

EnvCard2RealCard = {3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
                    8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q',
                    13: 'K', 14: 'A', 17: '2', 20: 'X', 30: 'D'}

RealCard2EnvCard = {'3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                    '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12,
                    'K': 13, 'A': 14, '2': 17, 'X': 20, 'D': 30}

AllEnvCard = [3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7,
              8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 11, 11, 11, 11, 12,
              12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14, 17, 17, 17, 17, 20, 30]

AllCards = ['rD', 'bX', 'b2', 'r2', 'bA', 'rA', 'bK', 'rK', 'bQ', 'rQ', 'bJ', 'rJ', 'bT', 'rT',
            'b9', 'r9', 'b8', 'r8', 'b7', 'r7', 'b6', 'r6', 'b5', 'r5', 'b4', 'r4', 'b3', 'r3']


class MyPyQT_Form(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(MyPyQT_Form, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint |    # 使能最小化按钮
                            QtCore.Qt.WindowCloseButtonHint |       # 使能关闭按钮
                            QtCore.Qt.WindowStaysOnTopHint)         # 窗体总在最前端
        self.setFixedSize(self.width(), self.height())              # 固定窗体大小
        self.setWindowIcon(QIcon('pics/favicon.ico'))
        window_pale = QtGui.QPalette()
        window_pale.setBrush(self.backgroundRole(), QtGui.QBrush(QtGui.QPixmap("pics/bg.png")))
        self.setPalette(window_pale)

        self.Players = [self.RPlayer, self.Player, self.LPlayer]
        self.counter = QTime()

        # 参数
        self.MyConfidence = 0.95  # 我的牌的置信度
        self.OtherConfidence = 0.849  # 别人的牌的置信度
        self.WhiteConfidence = 0.9  # 检测白块的置信度
        self.PassConfidence = 0.8  # 检测不出的置信度
        self.LandlordFlagConfidence = 0.9     # # 检测地主标志的置信度
        self.ThreeLandlordCardsConfidence = 0.9  # 检测地主底牌的置信度
        self.WaitTime = 1  # 等待状态稳定延时
        # 炸弹2s进稳态，其他大约1.5s
        self.MyFilter = 40  # 我的牌检测结果过滤参数
        self.OtherFilter = 10  # 别人的牌检测结果过滤参数
        self.SleepTime = 0.1  # 循环中睡眠时间

        # 坐标
        self.MyHandCardsPos = (324, 755, 1131, 70) # (414, 804, 1041, 59)  # 我的截图区域
        self.LPlayedCardsPos = (300, 330, 380, 115) # (530, 470, 380, 160)  # 左边截图区域
        self.RPlayedCardsPos = (1250, 330, 380, 115) # (1010, 470, 380, 160)  # 右边截图区域
        self.LandlordFlagPos = [(1409, 157, 90, 90), (32, 675, 90, 90), (130, 157, 90, 90)]#[(1320, 300, 110, 140), (320, 720, 110, 140), (500, 300, 110, 140)]  # 地主标志截图区域(右-我-左)
        self.ThreeLandlordCardsPos = (850, 68, 220, 110) # resize到0.67倍，148x74 #(817, 36, 287, 136)      # 地主底牌截图区域，resize成349x168
# 22AJTT9887744333
        # 信号量
        self.shouldExit = 0  # 通知上一轮记牌结束
        self.canRecord = threading.Lock()  # 开始记牌

        # 模型路径
        self.card_play_model_path_dict = {
            'landlord': "baselines/douzero_WP/landlord.ckpt",
            'landlord_up': "baselines/douzero_WP/landlord_up.ckpt",
            'landlord_down': "baselines/douzero_WP/landlord_down.ckpt"
        }

    def init_display(self):
        self.WinRate.setText("胜率：--%")
        self.InitCard.setText("开始")
        self.UserHandCards.setText("手牌")
        self.LPlayedCard.setText("上家出牌区域")
        self.RPlayedCard.setText("下家出牌区域")
        self.PredictedCard.setText("AI出牌区域")
        self.ThreeLandlordCards.setText("三张底牌")
        for player in self.Players:
            player.setStyleSheet('background-color: rgba(255, 0, 0, 0);')

    def init_cards(self):
        self.log_path = f"logs/{datetime.datetime.now().strftime('%Y%m%d@%H%M%S')}"
        os.makedirs(self.log_path,exist_ok=True)
        # 玩家手牌
        self.user_hand_cards_real = ""
        self.user_hand_cards_env = []
        # 其他玩家出牌
        self.other_played_cards_real = ""
        self.other_played_cards_env = []
        # 其他玩家手牌（整副牌减去玩家手牌，后续再减掉历史出牌）
        self.other_hand_cards = []
        # 三张底牌
        self.three_landlord_cards_real = ""
        self.three_landlord_cards_env = []
        # 玩家角色代码：0-地主上家, 1-地主, 2-地主下家
        self.user_position_code = None
        self.user_position = ""
        # 开局时三个玩家的手牌
        self.card_play_data_list = {}
        # 出牌顺序：0-玩家出牌, 1-玩家下家出牌, 2-玩家上家出牌
        self.play_order = 0

        self.env = None

        # 识别玩家手牌
        self.user_hand_cards_real = self.find_my_cards(self.MyHandCardsPos)
        self.UserHandCards.setText(self.user_hand_cards_real)
        self.user_hand_cards_env = [RealCard2EnvCard[c] for c in list(self.user_hand_cards_real)]
        # 识别三张底牌
        self.three_landlord_cards_real = self.find_three_landlord_cards(self.ThreeLandlordCardsPos)
        self.ThreeLandlordCards.setText("底牌：" + self.three_landlord_cards_real)
        self.three_landlord_cards_env = [RealCard2EnvCard[c] for c in list(self.three_landlord_cards_real)]
        # 识别玩家的角色
        self.user_position_code = self.find_landlord(self.LandlordFlagPos)
        if self.user_position_code is None:
            items = ("地主上家", "地主", "地主下家")
            item, okPressed = QInputDialog.getItem(self, "选择角色", "未识别到地主，请手动选择角色:", items, 0, False)
            if okPressed and item:
                self.user_position_code = items.index(item)
            else:
                return
        self.user_position = ['landlord_up', 'landlord', 'landlord_down'][self.user_position_code]
        for player in self.Players:
            player.setStyleSheet('background-color: rgba(255, 0, 0, 0);')
        self.Players[self.user_position_code].setStyleSheet('background-color: rgba(255, 0, 0, 0.1);')

        # 整副牌减去玩家手上的牌，就是其他人的手牌,再分配给另外两个角色（如何分配对AI判断没有影响）
        for i in set(AllEnvCard):
            self.other_hand_cards.extend([i] * (AllEnvCard.count(i) - self.user_hand_cards_env.count(i)))
        self.card_play_data_list.update({
            'three_landlord_cards': self.three_landlord_cards_env,
            ['landlord_up', 'landlord', 'landlord_down'][(self.user_position_code + 0) % 3]:
                self.user_hand_cards_env,
            ['landlord_up', 'landlord', 'landlord_down'][(self.user_position_code + 1) % 3]:
                self.other_hand_cards[0:17] if (self.user_position_code + 1) % 3 != 1 else self.other_hand_cards[17:],
            ['landlord_up', 'landlord', 'landlord_down'][(self.user_position_code + 2) % 3]:
                self.other_hand_cards[0:17] if (self.user_position_code + 1) % 3 == 1 else self.other_hand_cards[17:]
        })
        print(self.card_play_data_list)
        # 生成手牌结束，校验手牌数量
        if len(self.card_play_data_list["three_landlord_cards"]) != 3:
            QMessageBox.critical(self, "底牌识别出错", "底牌必须是3张！", QMessageBox.Yes, QMessageBox.Yes)
            self.init_display()
            return
        if len(self.card_play_data_list["landlord_up"]) != 17 or \
            len(self.card_play_data_list["landlord_down"]) != 17 or \
            len(self.card_play_data_list["landlord"]) != 20:
            QMessageBox.critical(self, "手牌识别出错", "初始手牌数目有误", QMessageBox.Yes, QMessageBox.Yes)
            self.init_display()
            return
        # 得到出牌顺序
        self.play_order = 0 if self.user_position == "landlord" else 1 if self.user_position == "landlord_up" else 2

        # 创建一个代表玩家的AI
        ai_players = [0, 0]
        ai_players[0] = self.user_position
        ai_players[1] = DeepAgent(self.user_position, self.card_play_model_path_dict[self.user_position])

        self.env = GameEnv(ai_players)

        self.start()

    def start(self):
        self.env.card_play_init(self.card_play_data_list)
        self.other_shots_count = 0
        self.white_check_count = 0
        print("开始出牌\n")
        #datetime.datetime.now().strftime("%Y%m%d@%H%M%S")
        print(self.play_order)
        while not self.env.game_over:
            # 玩家出牌时就通过智能体获取action，否则通过识别获取其他玩家出牌
            if self.play_order == 0:
                self.PredictedCard.setText("...")
                action_message = self.env.step(self.user_position)
                # 更新界面
                self.UserHandCards.setText("手牌：" + str(''.join(
                    [EnvCard2RealCard[c] for c in self.env.info_sets[self.user_position].player_hand_cards]))[::-1])

                self.PredictedCard.setText(action_message["action"] if action_message["action"] else "不出")
                self.WinRate.setText("胜率：" + action_message["win_rate"])
                print("\n手牌：", str(''.join(
                        [EnvCard2RealCard[c] for c in self.env.info_sets[self.user_position].player_hand_cards])))
                print("出牌：", action_message["action"] if action_message["action"] else "不出", "， 胜率：",
                      action_message["win_rate"])
                while self.have_white(self.RPlayedCardsPos) or self.check_pass(self.RPlayedCardsPos):
                    # 下家如果还停留在上一次的出牌状态，就说明我还没出（但是可能也需要一个手动切换的。。。如果下家出牌太快的话
                    # \
                        # pyautogui.locateOnScreen('pics_yysls/pass.png',
                        #                          region=self.RPlayedCardsPos,
                        #                          confidence=self.LandlordFlagConfidence):
                    print("等待玩家出牌")
                    self.sleep(100)
                    if self.env.game_over:
                        break
                self.play_order = 1
            elif self.play_order == 1:
                self.RPlayedCard.setText("...")
                pass_flag = None
                while not self.have_white(self.RPlayedCardsPos) and not self.check_pass(self.RPlayedCardsPos):
                # 检测下家没有出牌，也没有出要不起，继续等待
                        # not pyautogui.locateOnScreen('pics_yysls/pass.png',
                        #                              region=self.RPlayedCardsPos,
                        #                              confidence=self.LandlordFlagConfidence):
                    print("等待下家出牌")
                    self.sleep(500)
                    if self.env.game_over:
                        break
                self.sleep(1200)
                # 不出
                try:
                    pass_flag = pyautogui.locateOnScreen('pics_yysls/pass.png',
                                                     region=self.RPlayedCardsPos,
                                                     confidence=self.LandlordFlagConfidence)
                    list(pass_flag)
                except:
                    pass_flag = None
                # 未找到"不出"
                if pass_flag is None:
                    # 识别下家出牌
                    self.other_played_cards_real = self.find_other_cards(self.RPlayedCardsPos)
                # 找到"不出"
                else:
                    self.other_played_cards_real = ""
                print("\n下家出牌：", self.other_played_cards_real)
                self.other_played_cards_env = [RealCard2EnvCard[c] for c in list(self.other_played_cards_real)]
                self.env.step(self.user_position, self.other_played_cards_env)
                # 更新界面
                self.RPlayedCard.setText(self.other_played_cards_real if self.other_played_cards_real else "不出")
                self.play_order = 2
            elif self.play_order == 2:
                self.LPlayedCard.setText("...")
                while not self.have_white(self.LPlayedCardsPos) and not self.check_pass(self.LPlayedCardsPos):
                # \
                        # not pyautogui.locateOnScreen('pics_yysls/pass.png',
                                                    # region=self.LPlayedCardsPos,
                                                    # confidence=self.LandlordFlagConfidence):
                    print("等待上家出牌")
                    self.sleep(500)
                    if self.env.game_over:
                        break
                self.sleep(1200)
                # 不出
                try:
                    pass_flag = pyautogui.locateOnScreen('pics_yysls/pass.png',
                                                     region=self.LPlayedCardsPos,
                                                     confidence=self.LandlordFlagConfidence)
                    list(pass_flag)
                except:
                    pass_flag = None
                # 未找到"不出"
                if pass_flag is None:
                    # 识别上家出牌
                    self.other_played_cards_real = self.find_other_cards(self.LPlayedCardsPos)
                # 找到"不出"
                else:
                    self.other_played_cards_real = ""
                print("\n上家出牌：", self.other_played_cards_real)
                self.other_played_cards_env = [RealCard2EnvCard[c] for c in list(self.other_played_cards_real)]
                self.env.step(self.user_position, self.other_played_cards_env)
                self.play_order = 0
                # 更新界面
                self.LPlayedCard.setText(self.other_played_cards_real if self.other_played_cards_real else "不出")
            else:
                pass

            self.sleep(100)

        print("{}胜，本局结束!\n".format("农民" if self.env.winner == "farmer" else "地主"))
        QMessageBox.information(self, "本局结束", "{}胜！".format("农民" if self.env.winner == "farmer" else "地主"),
                                QMessageBox.Yes, QMessageBox.Yes)
        self.env.reset()
        self.init_display()

    def sleep(self, ms):
        self.counter.restart()
        while self.counter.elapsed() < ms:
            QtWidgets.QApplication.processEvents(QEventLoop.AllEvents, 50)
    def find_landlord(self, landlord_flag_pos):
        for pos in landlord_flag_pos:
            try:
                result = pyautogui.locateOnScreen('pics_yysls/landlord_words.png', region=pos, grayscale=False, confidence=self.LandlordFlagConfidence)
                list(result)
                return landlord_flag_pos.index(pos)
            # if result is not None:
            except:
                pass
        return None

    def find_three_landlord_cards(self, pos):
        three_landlord_cards_real = ""
        img = pyautogui.screenshot(region=pos)
        img = img.resize((int(220*1.5),int(110*1.5)))#((349, 168))
        img.save(os.path.join(self.log_path,"landlord_cards.png"))
        # 需要调整
        for card in AllCards:
            print(card)
            try:
                result = pyautogui.locateAll(needleImage='pics_yysls/m' + card + '.png', haystackImage=img, grayscale=False, confidence=self.ThreeLandlordCardsConfidence)
                three_landlord_cards_real += card[1] * self.cards_filter(list(result), self.OtherFilter)
            except Exception as e:
                #print(e)
                pass
            print(three_landlord_cards_real)
        return three_landlord_cards_real

    def find_my_cards(self, pos):
        user_hand_cards_real = ""
        img = pyautogui.screenshot(region=pos)
        img.save(os.path.join(self.log_path,"my_cards.png"))
        for card in AllCards:
            print(card)
            try:
                result = pyautogui.locateAll(needleImage='pics_yysls/m' + card + '.png', haystackImage=img, grayscale=False, confidence=self.MyConfidence)
                #print(card, list(result))
                user_hand_cards_real += card[1] * self.cards_filter(list(result), self.MyFilter)
            except:
                pass
            print(user_hand_cards_real)
        return user_hand_cards_real

    def find_other_cards(self, pos):
        other_played_cards_real = ""

        self.sleep(500)

        img = pyautogui.screenshot(region=pos)
        img.save(os.path.join(self.log_path,f"other_cards_{self.other_shots_count}.png"))
        self.other_shots_count += 1
        for card in AllCards:
            try:
                result = pyautogui.locateAll(needleImage='pics_yysls/o' + card + '.png', haystackImage=img, grayscale=False, confidence=self.OtherConfidence)
                other_played_cards_real += card[1] * self.cards_filter(list(result), self.OtherFilter)
            except:
                pass
        return other_played_cards_real

    def cards_filter(self, location, distance):  # 牌检测结果滤波
        if len(location) == 0:
            return 0
        locList = [location[0][0]]
        count = 1
        for e in location:
            flag = 1  # “是新的”标志
            for have in locList:
                if abs(e[0] - have) <= distance:
                    flag = 0
                    break
            if flag:
                count += 1
                locList.append(e[0])
        return count

    def have_white(self, pos):  # 是否有白块
        img = pyautogui.screenshot(region=pos)
        img.save(os.path.join(self.log_path,f"white_check_{self.white_check_count}.png"))
        self.white_check_count += 1
        for card in ['1','2','3','4','D','X']:
            try:
                result = pyautogui.locateAll(needleImage=f'pics_yysls/o{card}.png', haystackImage=img, grayscale=False, confidence=self.WhiteConfidence)
                # result = pyautogui.locateOnScreen('pics_yysls/white.png', region=pos, grayscale=False, confidence=self.WhiteConfidence)
                print(list(result))
                return True
            except:
                pass
        return False
        # if result is None:
        #     return 0
        # else:
        #     return 1

    def check_pass(self, pos):
        try:
            result = pyautogui.locateOnScreen('pics_yysls/pass.png', region=pos, confidence=self.PassConfidence)
            list(result)
            return True
        except:
            return False

    def stop(self):
        try:
            self.env.game_over = True
        except AttributeError as e:
            print(e)
            pass 
            


if __name__ == '__main__':

    # os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    # os.environ["CUDA_VISIBLE_DEVICES"] = '0'
    os.environ["GIT_PYTHON_REFRESH"] = 'quiet'

    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("""
    QPushButton{
        text-align : center;
        background-color : white;
        font: bold;
        border-color: gray;
        border-width: 2px;
        border-radius: 10px;
        padding: 6px;
        height : 14px;
        border-style: outset;
        font : 14px;
    }
    QPushButton:hover{
        background-color : light gray;
    }
    QPushButton:pressed{
        text-align : center;
        background-color : gray;
        font: bold;
        border-color: gray;
        border-width: 2px;
        border-radius: 10px;
        padding: 6px;
        height : 14px;
        border-style: outset;
        font : 14px;
        padding-left:9px;
        padding-top:9px;
    }
    QComboBox{
        background:transparent;
        border: 1px solid rgba(200, 200, 200, 100);
        font-weight: bold;
    }
    QComboBox:drop-down{
        border: 0px;
    }
    QComboBox QAbstractItemView:item{
        height: 30px;
    }
    QLabel{
        background:transparent;
        font-weight: bold;
    }
    """)
    my_pyqt_form = MyPyQT_Form()
    my_pyqt_form.show()
    sys.exit(app.exec_())
