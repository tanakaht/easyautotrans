import sys
import os
import time
import re
from pathlib import Path
import pyperclip
from googletrans import Translator
import argparse
from functools import partial
from termcolor import cprint, HIGHLIGHTS, COLORS
from pynput import mouse, keyboard
 

SAVE_PATH = Path('~/paper_translated/tmp/tmp.md').expanduser()
keyboard_controller = keyboard.Controller()

def create_parser():
    parser = argparse.ArgumentParser(
        description="コピーした英文を翻訳")
    # corpus path and preprocessing
    parser.add_argument('--mode', type=str,  default='manual_copy',
                        help="""modeを選択(default:manual_copy)
                         manual_copy: 自分でコピー
                         auto_copy: dragすると勝手にコピー""")
    parser.add_argument('--color', type=str,  default='green',
                        help="find text ~ の文字色を指定") 
    parser.add_argument('--on_color', type=str,  default=None,
                        help="find text ~ の下地の色を指定") 
    return parser

class AutoCopy:
    def __init__(self, on_drag, color='green', on_color=None):
        self.x = 0
        self.y = 0
        self.on_drag = on_drag
        self.color = color
        self.on_color = on_color

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.x = x
            self.y = y
        else:
            if self.x != x or self.y != y:
                self.on_drag(color=self.color, on_color=self.on_color)

    def run(self):
        with mouse.Listener(on_click=self.on_click) as listener: 
            try: 
                listener.join() 
            except KeyboardInterrupt: 
                listener.stop()
                print("\nBye.")
                sys.exit(0)

class ManualCopy:
    def __init__(self, on_copy, color='green', on_color=None):
        self.clip_pre = ''
        self.clip_now = ''
        self.on_copy = on_copy
        self.color = color
        self.on_color = on_color

    def run(self):
        self.clip_pre = pyperclip.paste()
        cprint("give me text on clipboard... [quit:Ctrl+C]", color=self.color, on_color=self.on_color, attrs=['bold'], end='\r')
        try: 
            while True:
                self.clip_now = pyperclip.paste()
                if self.clip_pre == self.clip_now:
                    time.sleep(1)
                else:
                    self.on_copy(self.clip_now, color=self.color, on_color=self.on_color)
                    self.clip_pre = self.clip_now
        except KeyboardInterrupt: 
            print("\nBye.")
            sys.exit(0)

def on_copy(text, color='green', on_color=None):
    try:
        cprint("find text on clipboard! translating into Japanese..." , color=color, on_color=on_color, attrs=['bold'])
        print(trans_text(modify_text_for_translate(text)))
        cprint("give me text on clipboard... [quit:Ctrl+C]", color=color, on_color=on_color, attrs=['bold'], end='\r')
    except Exception as e:
        print(e)

def on_drag(color='green', on_color=None):
    # コピーする
    # mac, linux
    if os.name == 'posix':
        with keyboard_controller.pressed(keyboard.Key.cmd):
            keyboard_controller.press('c')
    # windows
    if os.name == 'nt':
        with keyboard_controller.pressed(keyboard.Key.ctrl):
            keyboard_controller.press('c')
    # コピーされるまで少し時間が必要
    time.sleep(0.01)
    clip = pyperclip.paste()
    on_copy(clip, color=color, on_color=on_color)

def modify_text_for_translate(input_text):
    dic = {
        '- ': '', # 行区切りのハイフンを全消去
        # for CRLF
        '-\r\n': '', # 行区切りのハイフン除去
        '\r\n': ' ', # 改行->空白変換
        # for CR
        '-\r': '', # 行区切りのハイフン除去
        '\r': ' ', # 改行->空白変換
        # for LF
        '-\n': '', # 行区切りのハイフン除去
        '\n': ' '  # 改行->空白変換
    }
    prg = re.compile('|'.join(dic.keys()))
    formatter = lambda match: dic[match.group(0)]
    # 一気に整形
    text = prg.sub(formatter, input_text)

    # .を含む特殊な表現を一時的に置換する
    dic = {
        'e.g.': 'e_g_',
        'et al.': 'et al_',
        'cf.': 'cf_',
        'i.e.': 'i_e_',
        'Fig.': 'Fig_',
        '.js': '_js',
        'etc.': 'etc_'
    }
    # .を含む数字群の追加
    for i in range(10):
        dic[f'{i}.'] = f'{i}_'

    # 一時的に置換
    for word in dic:
        text = text.replace(word, dic[word])

    # 文末はダブル改行
    text = re.sub('[.:;][)”\"\']?', '\g<0>\n\n', text)
    
    # .を含む特殊な表現を元に戻す
    for word in dic:
        text = text.replace(dic[word], word)

    # 改行後に行頭が小文字になるのは改行がおかしいので元に戻す
    for match in re.finditer('\n\n[a-z/]' ,text):
        text = re.sub('\n\n[a-z/]', match.group(0)[-1:], text, count=1)
    for match in re.finditer('\n\n [a-z0-9]' ,text):
        text = re.sub('\n\n [a-z0-9]', match.group(0)[-2:], text, count=1)

    # 行頭のスペースを取り除く
    text = text.replace('\n\n ', '\n\n')
    return text

# 原文こみ
def trans_text(text):
    raw_trans = Translator().translate(text, dest = 'ja').text
    original = [sentence for sentence in text.split('\n') if sentence != '']
    translated = [sentence for sentence in raw_trans.split('\n') if sentence != '']
    return '\n'.join([f'{t1}\n{t2}\n' for t1, t2 in zip(original, translated)])

def main():
    parser = create_parser()
    args = parser.parse_args()

    # 色のチェック
    if not (args.color in COLORS or args.color is None):
        print(f"KeyError: no such color with {args.on_color}")
        return
    if not (args.on_color in HIGHLIGHTS or args.on_color is None):
        print(f"KeyError: no such color with {args.on_color}")
        return

    modes = {
        'manual_copy': ManualCopy(on_copy, args.color, args.on_color),
        'auto_copy': AutoCopy(on_drag, args.color, args.on_color)
    }
    try:
        model = modes[args.mode]
    except KeyError:
        print(f"KeyError: no such mode with {args.mode}")
        return
    
    model.run()

if __name__ == '__main__':
  main()
