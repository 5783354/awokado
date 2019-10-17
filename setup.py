from importlib.machinery import SourceFileLoader
from os import path

from setuptools import setup


VERSION = SourceFileLoader(
    "version", path.join(".", "awokado", "version.py")
).load_module()

VERSION = VERSION.__version__

with open("README.md", "r") as fh:
    long_description = fh.read()

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
    install_requires=(
        "bcrypt",
        "bulky",
        "boto3",
        "cached-property",
        "dynaconf",
        "falcon==2.0.0",
        "marshmallow>=3.0.0rc5",
        "pyaml",
        "clavis",
        "apispec==2.0.1",
        "jinja2",
        "SQLAlchemy>=1.3.0",
        "m2r",
    ),
    python_requires=">=3.7",
)
