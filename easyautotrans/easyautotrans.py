import time
import pyperclip
from googletrans import Translator as GoogleTrans
import argparse
from termcolor import cprint
from typing import List, Tuple, Optional
import nltk
import deepl
import os
import re
import traceback
import getpass
from logging import LogRecord, getLogger, StreamHandler, FileHandler, DEBUG

nltk.download('punkt', quiet=True)

if not os.path.exists(os.path.expanduser("~/.easyautotrans")):
    os.mkdir(os.path.expanduser('~/.easyautotrans'))
logger = getLogger(__name__)
handler = FileHandler(os.path.expanduser("~/.easyautotrans/log"))
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)


def create_parser():
    parser = argparse.ArgumentParser(
        description="コピーした英文を翻訳")
    parser.add_argument('--translator', type=str,  default='googletrans',
                        help="""Choose your translator from googletrans, or deepl.(default:googletrans)""")
    return parser

class Printer:
    """
    特に意味ない。Stdout以外のUI開発したくなった時のためにIFだけ確認。
    """
    def print_event(self, s: str, **kwargs):
        raise NotImplementedError

    def print_text(self, s: str, **kwargs):
        raise NotImplementedError

    def print_content(self, content: List[Tuple[str]], **kwargs):
        raise NotImplementedError

    def print_log(self, s: str, **kwargs):
        raise NotImplementedError

class StdoutPrinter(Printer):
    def __init__(self, event_color: Optional[str]="green", text_color: Optional[str]=None, log_color: Optional[str]=None, output_log=False):
        super().__init__()
        self.event_color = event_color
        self.text_color = text_color
        self.log_color = log_color
        self.output_log = output_log
        return

    def print_event(self, s: str, **kwargs):
        cprint(s, self.event_color, attrs=['bold'], **kwargs)

    def print_text(self, s: str, **kwargs):
        cprint(s, self.text_color, **kwargs)

    def print_content(self, content: List[Tuple[str]], **kwargs):
        for raw_sentence, translated_sentence in content:
            cprint(raw_sentence, self.text_color, **kwargs)
            cprint(translated_sentence, self.text_color, **kwargs)
            cprint("", self.text_color, **kwargs)

    def print_log(self, s: str, **kwargs):
        if self.output_log:
            cprint(s, self.log_color, **kwargs)


class Translator:
    def __init__(self, mode="googletrans"):
        self.mode = mode
        self.translator = self.get_translator()
        dic = {
            # '- ': '', # 行区切りのハイフンを全消去 <-これ何?
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
        self.prg = re.compile('|'.join(dic.keys()))
        self.formatter = lambda match: dic[match.group(0)]

    def get_translator(self):
        raise NotImplementedError

    def translate(self, raw_text: str) -> List[Tuple[str]]:
        ret = []
        sentences = nltk.sent_tokenize(self.modify_text(raw_text))
        try:
            for sentence in sentences:
                translated_sentence = self._translate(sentence)
                ret.append((sentence, translated_sentence))
            return ret
        except Exception as e: # TODO: errorの種類をちゃんとする
            logger.info(f"{e} {self}")
            logger.info(traceback.format_exc()+"\n\n")
            print(e)
            return ret

    def _translate(self, sentence: str) -> str:
        raise NotImplementedError

    def modify_text(self, raw_text: str) -> str:
        # 一気に整形
        text = self.prg.sub(self.formatter, raw_text)
        return text


class GoogleTranslator(Translator):
    def get_translator(self):
        return GoogleTrans()

    def _translate(self, sentence: str) -> str:
        # TODO: エラーハンドリング
        try:
            translated_sentence = self.translator.translate(sentence, dest = 'ja').text
        except Exception as e:
            logger.info(f"{e} {self}")
            logger.info(traceback.format_exc()+"\n\n")
            translated_sentence = str(e) # TODO: retry
        return translated_sentence


class DeeplTranslator(Translator):
    def get_translator(self):
        # TODO: errorの際、キーを取り直す
        auth_key = self.get_auth_key()
        return deepl.Translator(auth_key)

    def get_auth_key(self) -> str:
        try:
            return self.load_auth_key()
        except FileNotFoundError:
            self.save_auth_key()
            return self.load_auth_key()

    def save_auth_key(self) -> None:
        auth_key = getpass.getpass("auth key> ")
        with open(os.path.expanduser("~/.easyautotrans/deepl_auth_key"), "w") as f:
            f.write(auth_key)

    def load_auth_key(self) -> str:
        if os.path.exists(os.path.expanduser("~/.easyautotrans/deepl_auth_key")):
            with open(os.path.expanduser("~/.easyautotrans/deepl_auth_key"), "r") as f:
                auth_key = f.read()
            return auth_key
        else:
            raise FileNotFoundError

    def _translate(self, sentence: str) -> str:
        # TODO: エラーハンドリング
        try:
            translated_sentence = self.translator.translate_text(sentence, target_lang="ja").text
        except Exception as e:
            logger.info(f"{e} {self}")
            logger.info(traceback.format_exc()+"\n\n")
            translated_sentence = str(e) # TODO: retry
        return translated_sentence

class ClipboardListener:
    def __init__(self, printer: Printer, translator: Translator):
        self.printer = printer
        self.translator = translator
        self.deray = 1
        self.n_retry = 3
        return

    def func(self, s: str):
        """clipboard変更時に走らす関数"""
        self.printer.print_content(self.translator.translate(s))

    # TODO: clipboardの変化ではなく、cmd+cとかで呼び出す
    # TODO: clipboardのイベントリスナーで探す
    def run(self):
        clip_pre = pyperclip.paste()
        try:
            while True:
                clip_new = pyperclip.paste()
                if clip_pre == clip_new:
                    self.printer.print_event("give me text on clipboard... [quit:Ctrl+C]", end='\r')
                    time.sleep(self.deray)
                    continue
                self.printer.print_event("find text on clipboard! translating into Japanese..." )
                for err_cnt in range(self.n_retry):
                    try:
                        self.func(clip_new)
                        break
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    except Exception as e:
                        logger.info(f"{e} {self}")
                        logger.info(traceback.format_exc()+"\n\n")
                        translated_sentence = str(e) # TODO: retry
                        if err_cnt == self.n_retry-1:
                            self.printer.print_event(f"failed({e})")
                        else:
                            self.printer.print_log(f"retry({e})")
                clip_pre = clip_new
        except KeyboardInterrupt:
            self.printer.print_event("\nBye.")

def main():
    parser = create_parser()
    args = parser.parse_args()
    assert args.translator in "googletrans deepl".split()
    printer = StdoutPrinter()
    if args.translator=="googletrans":
        translator = GoogleTranslator()
    elif args.translator=="deepl":
        translator = DeeplTranslator()
    listener = ClipboardListener(printer, translator)
    listener.run()


if __name__ == '__main__':
    main()
