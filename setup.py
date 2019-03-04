import setuptools
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="awokado",
    version="0.3b5",
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
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ),
    keywords=" ".join(
        sorted(
            {"api", "rest", "wsgi", "falcon", "sqlalchemy", "sqlalchemy-core"}
        )
    ),
    package_dir={'': 'awokado'},
    packages=setuptools.find_packages(where="awokado"),
    install_requires=(
        "bcrypt",
        "boto3",
        "dynaconf",
        "falcon",
        "marshmallow>=3.0.0rc3",
        "pyaml",
        "PyJWT",
        "clavis",
        "python-jose",
        "apispec",
        "jinja2",
    ),
    python_requires=">=3.6",
)
