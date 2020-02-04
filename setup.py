import setuptools

version = '1.0.8'

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='moneydashboard',
    version=version,
    description='MoneyDashboard library for accessing its API',
    author='Martin Brooksbank',
    author_email='martin@flamedevelopment.co.uk',
    url='https://github.com/shutupflanders/moneydashboard',
    keywords=['money dashboard', 'financial', 'money'],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
