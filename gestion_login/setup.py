from setuptools import setup,find_packages

setup(
    name="gestion_login",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires =[
        "Flask","Flask-SQLAlchemy","Werkzeug", "Flask-Login","Flask-Mail","itsdangerous"
    ],

)