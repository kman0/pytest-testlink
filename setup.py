__author__ = 'M'
from setuptools import setup
import codecs

long_description = 'pytest-testlink is a plugin for py.test that reports to testlink'

VERSION = '0.2'
PYPI_VERSION = '0.2'

setup(
    name='pytest-testlink',
    description=long_description,
    long_description=long_description,
    version=VERSION,
    url='https://github.com/manojklm/pytest-testlink/',
    download_url='https://github.com/manojklm/pytest-testlink/tarball/%s' % PYPI_VERSION,
    license='MIT',
    author='mk',
    author_email='manojklm@gmail.com',
    py_modules=['pytest_testlink'],
    entry_points={'pytest11': ['testlink = pytest_testlink']},
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=['pytest>=2.6'],
    classifiers=[
        'Environment :: Plugins',
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ]
)
