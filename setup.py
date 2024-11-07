from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in tessuto_hr/__init__.py
from tessuto_hr import __version__ as version

setup(
	name="tessuto_hr",
	version=version,
	description="Tessuto Hr",
	author="safdar ali",
	author_email="safdar211@gmil.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
