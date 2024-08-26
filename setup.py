from setuptools import setup

setup(
    name='Teccel Setup',
    version='1.0',
    packages=find_packages(),
    install_requires=['numpy','pandas','streamlit','gspread']
)