import sys

from setuptools import setup, find_packages
from dragoneye.version import __version__

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read().splitlines()

project_name = 'dragoneye'
with open("README.md", "r") as fh:
    long_description = fh.read()
version = __version__

if "--version" in sys.argv:
    index = sys.argv.index('--version')
    version = sys.argv[index + 1]
    sys.argv.remove("--version")
    sys.argv.remove(version)

setup(
    name=project_name,
    description='Multi-cloud data scan tool',
    long_description=long_description,
    long_description_content_type="text/markdown",
    version=version,
    author='Indeni',
    author_email='engineering@indeni.com',
    url='https://github.com/indeni/dragoneye',
    packages=find_packages(include=[project_name, f'{project_name}.*']),
    package_data={'': ['config.yaml']},
    include_package_data=True,
    keywords=['cloud', 'aws', 'azure', 'scan'],
    install_requires=requirements,
    entry_points={
        'console_scripts': [f'{project_name}=dragoneye.scan:safe_cli_entry_point']
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
