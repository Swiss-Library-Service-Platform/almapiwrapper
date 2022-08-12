from setuptools import find_packages, setup

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text()

setup(name='almapiwrapper',
      version='0.5.7',
      long_description=long_description,
      long_description_content_type='text/reST',
      packages=find_packages(),
      py_modules=['almapiwrapper'],
      )
