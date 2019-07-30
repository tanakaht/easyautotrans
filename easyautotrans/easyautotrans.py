import sys
import time
import re
from pathlib import Path
import pyperclip
from googletrans import Translator
import argparse
from functools import partial
from termcolor import cprint, HIGHLIGHTS


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
    parser.add_argument('--on_color', type=str,  default=None,
                        help="find text ~ の下地の色を指定") 
    return parser

# clip変更のたびfunc(clip)実行
def watch_clipboard(func, on_color=None):
    clip_tmp = pyperclip.paste()
    try:
        while True:
            clip_now = pyperclip.paste()
            if clip_tmp == clip_now:
                cprint("give me text on clipboard... [quit:Ctrl+C]", 'green', attrs=['bold'], end='\r')
                time.sleep(1)
                continue
            try:
                cprint("find text on clipboard! translating into Japanese..." , 'green', on_color=on_color, attrs=['bold'])
                # 翻訳
                en_text = trans_text(modify_text_for_translate(clip_now))
                func(text=en_text)
            except Exception as e:
                print(e)
            clip_tmp = clip_now
    except KeyboardInterrupt:
        print("\nBye.")
        sys.exit(0)

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

def print_translated_text(text):
    write2files(text)

def write_translated_text(text, io_file):
    write2files(text, io_file)

def print_and_write(text, io_file):
    write2files(text, sys.stdout, io_file)

# 書き出し関数
def write2files(text, *files):
    """
    :param text: 出力したいテキスト(str)
    :param files: 出力したいファイル(like IOBase)
    :return: None, filesにtextを書き出す
    """
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
        return
    
    if not (args.on_color in HIGHLIGHTS or args.on_color is None):
        print(f"KeyError: no such color with {args.on_color}")
        return

    if args.mode == 'print':
        watch_clipboard(writer, on_color=args.on_color)

    else:
        print(f'SAVE PATH: "{args.file}"')
        save_dir = Path(args.file).parent.expanduser()
        if not save_dir.exists():
            save_dir.mkdir(parents=True)

        with open(args.file, 'w') as f:
            watch_clipboard(partial(writer, io_file=f), on_color=args.on_color)

if __name__ == '__main__':
  main()
