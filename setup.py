from setuptools import setup, find_packages

setup(
    name="cloudify_tester",
    version="0.1.0",
    package_dir={'': 'src'},
    packages=find_packages('src'),
    package_data={'cloudify_tester': [
        'schemas/*.yaml',
    ]},
    install_requires=[
        'pytest',
        'PyYAML==3.11',
    ],
)
