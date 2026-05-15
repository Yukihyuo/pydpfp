from pathlib import Path

from setuptools import setup


BASE_DIR = Path(__file__).resolve().parent
README_PATH = BASE_DIR / "README.md"

long_description = "Python wrapper for DigitalPersona fingerprint reader and FingerJet libraries."
if README_PATH.exists():
	long_description = README_PATH.read_text(encoding="utf-8")


setup(
	name="pydpfp",
	version="0.1.0",
	author="Yukihyuo",
	description="Windows wrapper for DigitalPersona fingerprint hardware (dpfpdd/dpfj).",
	long_description=long_description,
	long_description_content_type="text/markdown",
	packages=["pydpfp"],
	include_package_data=True,
	package_data={
		"pydpfp": ["*.dll"],
	},
	python_requires=">=3.9",
	classifiers=[
		"Development Status :: 3 - Alpha",
		"Intended Audience :: Developers",
		"Operating System :: Microsoft :: Windows",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3 :: Only",
		"Programming Language :: Python :: 3.9",
		"Programming Language :: Python :: 3.10",
		"Programming Language :: Python :: 3.11",
		"Programming Language :: Python :: 3.12",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Topic :: System :: Hardware",
	],
	zip_safe=False,
)
