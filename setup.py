from setuptools import setup

setup(
    name="cloudify_tester",
    version="0.1.0",
    packages=['cloudify_tester'],
    package_data={'cloudify_tester': [
        'schemas/*.yaml',
    ]},
    install_requires=[
        'pytest',
        'pytest-bdd',
        'PyYAML==3.11',
        'cloudify>=3.4a5',
    ],
)
