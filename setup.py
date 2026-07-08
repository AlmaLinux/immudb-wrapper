from setuptools import setup

setup(
    name='immudb_wrapper',
    version='0.1.9',
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
        # immudb-py 1.5 pulls protobuf>=4, whose PEP420 `google` namespace is
        # broken by the stray `google-api` package immudb-py depends on, so
        # `import google.protobuf` fails. Cap at <1.5 and keep protobuf on the
        # 3.x line (pkg_resources namespace) which tolerates google-api.
        'immudb-py>=1.4.0,<1.5',
        'protobuf<4',
    ],
    python_requires='>=3.7',
)
