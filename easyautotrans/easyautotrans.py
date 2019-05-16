import sys, os
import time
from pathlib import Path
import pyperclip
from googletrans import Translator
import argparse
from functools import partial
# from pync import Notifier 通知に出そうとしたが見にくかった

SAVE_PATH = Path('~/paper_translated/tmp/tmp.md').expanduser()

def create_parser():
    parser = argparse.ArgumentParser(
        description="コピーした英文を翻訳")
    # corpus path and preprocessing
    parser.add_argument('--mode', type=str,  default='print',
                        help="""modeを選択(default:print)
                         print:terminalにprint
                         write:--fileに書き込み
                         print_and_write:どっちも""")
    parser.add_argument('--file', type=str,  default=str(SAVE_PATH),
                        help="書き込み先を指定")
    return parser


# clip変更のたびfunc(clip)実行
def watch_clipboard(func):
    clip_tmp = pyperclip.paste()
    while True:
        clip_now = pyperclip.paste()
        if clip_tmp == clip_now:
            continue
        try:
            print("copied")
            func(text=clip_now)
        except Exception as e:
            print(e)
        clip_tmp = clip_now
        time.sleep(1)


def modify_text_for_trancerate(text):
    # 段落以外の改行を削除
    text = text.replace(".\n", "\t")
    text = text.replace("\n", " ")
    text = text.replace("\t", ".\n")
    text = text.replace("  ", " ")
    text = text.replace("- ", "")
    # 一文ごと改行2つ
    text = text.replace(". ", ".\n\n")
    # pyperclip.copy(text)
    return text

# 日本語だけ
def trans_text_only_j(text):
    return Translator().translate(text, dest = 'ja').text

# 原文こみ
def trans_text(text):
    trans = Translator().translate(text, dest = 'ja').text
    text = [sentence for sentence in text.split('\n') if sentence != '']
    trans = [sentence for sentence in trans.split('\n') if sentence != '']
    print(len(text), len(trans))
    t = ''
    for t1, t2 in zip(text, trans):
        t += f'{t1}\n{t2}\n\n'
    return t

def print_translated_text(text):
    print(trans_text(modify_text_for_trancerate(text)))

def write_translated_text(text, f):
    f.write(trans_text(modify_text_for_trancerate(text)))

def print_and_write(text, f):
    text = trans_text(modify_text_for_trancerate(text))
    print(text)
    f.write(text)

def main():
    parser = create_parser()
    args = parser.parse_args()
    if args.mode == 'print':
        watch_clipboard(print_translated_text)
    elif args.mode == 'write':
        print(f'SAVE PATH: "{args.file}"')
        save_dir = Path(args.file).parent.expanduser()
        if not save_dir.exists():
            os.makedirs(str(save_dir))
        with open(args.file, 'w') as f:
            watch_clipboard(partial(write_translated_text, f=f))
        
    elif args.mode == 'print_and_write':
        print(f'SAVE PATH: "{args.file}"')
        save_dir = Path(args.file).parent.expanduser()
        if not save_dir.exists():
            os.makedirs(str(save_dir))
        with open(args.file, 'w') as f:
            watch_clipboard(partial(print_and_write, f=f))

if __name__ == '__main__':
  main()
