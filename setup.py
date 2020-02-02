
from setuptools import find_packages, setup


with open('README.md', 'r', encoding='utf-8') as file:
    long_description = file.read()


setup(

    name = 'zimscan',
    version = '0.1.1',
    packages = find_packages(),

    author = 'Johan Berdat',
    author_email = 'jojolebarjos@gmail.com',
    license = 'MIT',

    url = 'https://gitlab.com/jojolebarjos/zimscan',

    description = 'ZIM file iterator',
    long_description = long_description,
    long_description_content_type = 'text/markdown',

    keywords = [
        'zim',
        'iterator',
        'wikipedia',
        'gutenberg',
        'kiwix'
    ],

    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],

    install_requires = [],

    python_requires = '>=3.5',

)
