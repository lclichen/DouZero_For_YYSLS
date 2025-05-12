from PIL import Image

import pyautogui


def have_white(img):  # 是否有白块
    for card in ['1','2','3','4','D','X']:
        try:
            result = pyautogui.locateAll(needleImage=f'pics_yysls/o{card}.png', haystackImage=img, grayscale=False, confidence=0.9)
            list(result)
            return True
        except Exception as e:
            #print(e)
            pass
    return False
def check_pass(img):
    try:
        result = pyautogui.locateAll(needleImage='pics_yysls/pass.png', haystackImage=img, grayscale=False, confidence=0.8)
        list(result)
        return True
    except Exception as e:
        print(e)
        return False
for i in range(256):
    img_path = f"H:\git_repos\DouZero_For_HappyDouDiZhu\logs2\white_check_{i}.png"
    img_i = Image.open(img_path)
    print(i, have_white(img_i), check_pass(img_i))
