import time
import pyperclip
from googletrans import Translator as GoogleTranslator
import argparse
from termcolor import cprint
from typing import List, Tuple, Optional
import nltk

nltk.download('punkt', quiet=True)

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
        if mode == "googletrans":
            self.translator = GoogleTranslator()
        elif mode == "deepl":
            raise NotImplementedError("開発中")

    def translate(self, raw_text: str) -> List[Tuple[str]]:
        ret = []
        # TODO: 余分な改行とハイフン等を削除する?(modify_text_for_translate相当の操作)
        raw_sentences = nltk.sent_tokenize(raw_text)
        for raw_sentence in raw_sentences:
            translated_sentence = self.translator.translate(raw_sentence, dest = 'ja').text
            ret.append((raw_sentence, translated_sentence))
        return ret


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
    # TODO: argsで何かいじる?
    printer = StdoutPrinter()
    translator = Translator(mode=args.translator)
    listener = ClipboardListener(printer, translator)
    listener.run()


if __name__ == '__main__':
    main()
