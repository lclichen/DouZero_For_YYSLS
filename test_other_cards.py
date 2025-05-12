from PIL import Image

import pyautogui

AllCards = ['rD', 'bX', 'b2', 'r2', 'bA', 'rA', 'bK', 'rK', 'bQ', 'rQ', 'bJ', 'rJ', 'bT', 'rT',
            'b9', 'r9', 'b8', 'r8', 'b7', 'r7', 'b6', 'r6', 'b5', 'r5', 'b4', 'r4', 'b3', 'r3']
def cards_filter(location, distance):  # 牌检测结果滤波
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
def find_other_cards(img):
    other_played_cards_real = ""

    for card in AllCards:
        try:
            result = pyautogui.locateAll(needleImage='pics_yysls/o' + card + '.png', haystackImage=img, grayscale=False, confidence=0.849)
            other_played_cards_real += card[1] * cards_filter(list(result), 10)
            print(card, other_played_cards_real)
        except Exception as e:
            print(card, e)
    return other_played_cards_real
for i in range(20):
    img_path = f"H:\git_repos\DouZero_For_HappyDouDiZhu\logs/20250512@210221/other_cards_{i}.png"
    img_i = Image.open(img_path)
    print(i, find_other_cards(img_i))
exit()
def find_my_cards(img):
    other_played_cards_real = ""

    for card in AllCards:
        try:
            result = pyautogui.locateAll(needleImage='pics_yysls/m' + card + '.png', haystackImage=img, grayscale=False, confidence=0.9)
            other_played_cards_real += card[1] * cards_filter(list(result), 40)
            print(card, other_played_cards_real)
        except Exception as e:
            print(card, e)
    return other_played_cards_real

print("my", find_my_cards(Image.open("H:\git_repos\DouZero_For_HappyDouDiZhu\logs\my_cards.png")))