from setuptools import setup
import sys
def readme():
    with open('README.md') as f:
        return f.read()

version="0.2.0"
setup(name='stf',
    version=version,
    description='The simple test framework',
    long_description=readme(),
    keywords='automation test',
    url='https://github.com/nokia',
    download_url="https://github.com/nokia/STF/archive/{0}.tar.gz".format(version),
    author='Gemfield',
    author_email='gemfield@civilnet.cn',
    license='Apache License, Version 2.0',
    packages=['stf'],
    scripts=[
        'stf/bin/stf',
        'stf/bin/iniParser.py'
    ],
    install_requires=[
        'paramiko>=2.1',
        'scp',
        'colorlog',
        'subprocess32'
    ],
    classifiers  = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Topic :: Software Development :: Testing"
     ],
    include_package_data=True,
    zip_safe=False)

