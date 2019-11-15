import re
from importlib.machinery import SourceFileLoader
from os import path

from setuptools import setup


VERSION = SourceFileLoader(
    "version", path.join(".", "awokado", "version.py")
).load_module()

VERSION = VERSION.__version__

with open("README.md", "r") as fh:
    long_description = fh.read()


def parse_deps(deps):
    items = re.findall(r'([\w\-_]+) ?= ?"(.*)"', deps)
    requires = []
    for i in items:
        dep = i[0]
        if i[1] != "*":
            dep += i[1]
        requires.append(dep)
    return requires


with open("Pipfile") as f:
    text = f.read()

    block = re.findall(r"\[packages\](.*?)\[", text, re.DOTALL)
    install_requires = parse_deps(block[0]) if block else []

    block = re.findall(r"\[dev-packages\](.*?)\[", text, re.DOTALL)
    tests_require = parse_deps(block[0]) if block else []

setup(
    name="awokado",
    version=VERSION,
    description="Fast and flexible API framework based on Falcon and SQLAlchemy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/5783354/awokado",
    author="Dmitry Karnei",
    author_email="5783354@gmail.com",
    classifiers=(
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ),
    keywords=" ".join(
        sorted(
            {"api", "rest", "wsgi", "falcon", "sqlalchemy", "sqlalchemy-core"}
        )
    ),
    packages=["awokado", "awokado.documentation", "awokado.exceptions"],
    install_requires=install_requires,
    tests_require=tests_require,
    python_requires=">=3.7",
)
