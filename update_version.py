import almapiwrapper
import re
import subprocess
import os

version = almapiwrapper.__version__

# pyproject.toml
with open('pyproject.toml') as f:
    content = f.read()

content = re.sub(r'version = ".+"', f'version = "{version}"', content)

with open('pyproject.toml', 'w') as f:
    f.write(content)

# README.rst
with open('README.rst') as f:
    content = f.read()

content = re.sub(r'\* Version: \d+\.\d+\.\d+', f'* Version: {version}', content)

with open('README.rst', 'w') as f:
    f.write(content)

# index.rst
with open('docs/index.rst') as f:
    content = f.read()

content = re.sub(r'\* Version: \d+\.\d+\.\d+', f'* Version: {version}', content)

with open('docs/index.rst', 'w') as f:
    f.write(content)

os.system(f'{os.getcwd()}/docs/make.bat html')
os.system(f'{os.getcwd()}/docs/make.bat html')

os.system('git add .')
os.system(f'git commit -m "Create version {version}"')
os.system(f'git push')
#
# os.system('twine upload dist/*')