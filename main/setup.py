from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pico-nand-flasher",
    version="2.5.0",
    author="bobberdolle1",
    author_email="",
    description="A Raspberry Pi Pico based NAND Flash programmer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bobberdolle1/pico-nand-flasher",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pico-nand-flasher-cli=src.cli.cli_interface:main",
            "pico-nand-flasher-gui=src.gui.gui_interface:main",
        ],
    },
)
