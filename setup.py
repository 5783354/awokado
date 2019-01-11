from setuptools import setup

setup(
    name="awokado",
    version="0.1b4",
    description="Fast and flexible API framework based on Falcon and SQLAlchemy",
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
    packages=["awokado", "awokado.exceptions"],
    install_requires=(
        "boto3",
        "bcrypt",
        "falcon",
        "marshmallow",
        "pyaml",
        "python-jose",
        "stairs",
        "dynaconf",
    ),
    python_requires=">=3.6",
)
