from setuptools import setup

setup(
    name='esman',
    version='0.1',
    py_modules=['bulkinsert'],
    install_requires=[
        'Click',
        'elasticsearch',
        'jsonpickle',
        'graphviz',
        'geoip2',
        'python-dateutil'
    ],
    entry_points='''
        [console_scripts]
        bulkinsert=bulkinsert:insert
        elasticsearch=es:es
        es=es:es
    ''',
)