from setuptools import setup, find_packages

def _requires_from_file(filename):
    return open(filename).read().splitlines()

setup(
    name="easyautotrans",
    version='0.2.1',
    url="https://github.com/tanakaht/easyautotrans",
    packages=find_packages(),
    install_requires=_requires_from_file('requirements.txt'),
    entry_points={
        "console_scripts": [
            "easy-auto-trans = easyautotrans.easyautotrans:main"
        ]
    }
)
