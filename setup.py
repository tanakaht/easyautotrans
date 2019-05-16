from setuptools import setup

setup(
    name="easyautotrans",
    install_requires=[
        "pyperclip",
        "googletrans"
    ],
    entry_points={
        "console_scripts": [
            "easy-auto-trans = easyautotrans.easyautotrans:main"
        ]
    }
)