import os
from setuptools import setup
from src.claudia.versions import CLAUDIA_VERSION

current_directory = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(current_directory, 'src/claudia/README.md'), encoding='utf-8') as f:
        long_description = f.read()
except Exception:
    long_description = ''


def read_requirements():
    with open('src/claudia/requirements.txt') as req:
        content = req.read()
        requirements = content.split('\n')

    return requirements


setup(
    name='claudia',
    version=CLAUDIA_VERSION,
    description='Helper utility to manage local rippled mainnet networks',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Kausty Saxena",
    author_email="ksaxena@ripple.com",
    keywords="ripple xrpl python local mainnet",
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
    ]},
    include_package_data=True,
    entry_points='''
        [console_scripts]
        claudia=claudia.claudia:main
    '''
)
