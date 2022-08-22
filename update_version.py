import almapiwrapper
import re

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