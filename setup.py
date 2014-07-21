from setuptools import setup

setup(
    name='earlPipeline',
    version='0.0.1',
    author='Dmytro Bielievtsov',
    author_email='belevtsoff@gmail.com',
    packages=['earlpipeline', 'earlpipeline.backends'],
    #url='http://pypi.python.org/pypi/TowelStuff/',
    license='LICENSE',
    description='A simplistic backend-agnostic web application for visualizing and constructing modular data-processing pipelines',
    long_description=open('README').read(),
    include_package_data=True,
    install_requires=[
        "tornado",
        "logutils",
        "bidict >= 0.1.2"
    ],
)
