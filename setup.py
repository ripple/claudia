import os

from setuptools import setup

# from setuptools import setup

# from distutils.core import setup

from src.claudia.versions import CLAUDIA_VERSION
# from setuptools import setup, find_packages
# try:
#     from setuptools import setup, find_packages
# except ImportError:
#     from distutils.core import setup, find_packages

current_directory = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(current_directory, 'src/claudia/README.md'), encoding='utf-8') as f:
        long_description = f.read()
except Exception:
    long_description = ''


def read_requirements():
    # print(os.getcwd())
    with open('src/claudia/requirements.txt') as req:
        content = req.read()
        requirements = content.split('\n')

    return requirements


setup(
    name='claudia',
    version=CLAUDIA_VERSION,
    description='Helper utility to manage local rippled networks',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Kausty Saxena",
    author_email="ksaxena@ripple.com",
    keywords="ripple xrpl python local mainnet sidechain",
    url='https://xrpl.org/',
    download_url='https://github.com/ripple/claudia',
    py_modules=['claudia.claudia'],
    install_requires=read_requirements(),
    packages=['claudia'],
    package_dir={"claudia": "src/claudia"},
    package_data={'claudia': [
        "./requirements.txt",
        "./README.md",
        "./network_setup/**/*"
        # ,
        # "./features/*.feature",
        # "./javascript/**/*",
        # "./python/**/*",
        # "./ui/**/*",
        # "./.streamlit/**/*",
        # "./aws/**/*"
    ]},
    include_package_data=True,
    entry_points='''
        [console_scripts]
        claudia=claudia.claudia:main
    '''
)
