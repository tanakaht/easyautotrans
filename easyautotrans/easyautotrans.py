import sys
import time
import re
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
            print("give me text on clipboard... [quit:Ctrl+C]", end='\r')
            continue
        try:
            print("find text on clipboard! translating into Japanese...")
            # 翻訳
            en_text = trans_text(modify_text_for_translate(clip_now))
            func(text=en_text)
        except Exception as e:
            print(e)
        clip_tmp = clip_now
        time.sleep(1)

def modify_text_for_translate(input_text):
    dic = {
        '-\s+': '', # 行区切りのハイフンを全消去
        '\n': ' ' # 改行->空白変換
    }
    prg = re.compile('|'.join(dic.keys()))
    formatter = lambda match: dic[match.group(0)]
    # 一気に整形
    text = prg.sub(formatter, input_text)
    # 文末はダブル改行
    text = text.replace(". ", ".\n\n")
    return text

# 原文こみ
def trans_text(text):
    raw_trans = Translator().translate(text, dest = 'ja').text
    original = [sentence for sentence in text.split('\n') if sentence != '']
    translated = [sentence for sentence in raw_trans.split('\n') if sentence != '']
    return '\n'.join([f'{t1}\n{t2}\n' for t1, t2 in zip(original, translated)])

def print_translated_text(text):
    write2files(text)

def write_translated_text(text, io_file):
    write2files(text, io_file)

def print_and_write(text, io_file):
    write2files(text, sys.stdout, io_file)

def write2files(text, *files):
    if files:
        for f in files:
            print(text, file=f, flush=True)
    else:
        print(text)


def main():
    parser = create_parser()
    args = parser.parse_args()
    modes = {
        'print': print_translated_text,
        'write': write_translated_text,
        'print_and_write': print_and_write
    }
    try:
        writer = modes[args.mode]
    except KeyError:
        print(f"KeyError: no such mode with {args.mode}")

    if args.mode == 'print':
        watch_clipboard(writer)

    else:
        print(f'SAVE PATH: "{args.file}"')
        save_dir = Path(args.file).parent.expanduser()
        if not save_dir.exists():
            save_dir.mkdir(parents=True)

        with open(args.file, 'w') as f:
            watch_clipboard(partial(writer, io_file=f))

if __name__ == '__main__':
  main()
