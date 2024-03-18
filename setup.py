from setuptools import setup

setup(
    name='immudb_wrapper',
    version='0.1.2',
    author='Daniil Anfimov',
    author_email='anfimovdan@gmail.com',
    description=(
        'The wrapper around the SDK client immudb-py from project Codenotary, '
        'which expands the functionality of the original client '
        'with additional functions.'
    ),
    url='https://github.com/AlmaLinux/immudb-wrapper',
    project_urls={
        'Bug Tracker': 'https://github.com/AlmaLinux/immudb-wrapper/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: '
        'GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
    ],
    py_modules=['immudb_wrapper'],
    scripts=['immudb_wrapper.py'],
    install_requires=[
        'GitPython>=3.1.20',
        'immudb-py>=1.4.0',
        'googleapis-common-protos==1.61.0',
        'protobuf==3.20.3',
    ],
    python_requires='>=3.7',
)
