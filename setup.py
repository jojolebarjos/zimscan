
from setuptools import find_packages, setup

setup(

    name = 'zimscan',
    version = '0.0.1',
    packages = find_packages(),

    author = 'Jojo le Barjos',
    author_email = 'jojolebarjos@gmail.com',
    license_file = 'LICENSE',

    description = 'ZIM file iterator',

    keywords = [
        'zim',
        'iterator',
        'wikipedia',
        'gutenberg',
        'kiwix'
    ],

    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: Freely Distributable',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],

    install_requires = []

)
