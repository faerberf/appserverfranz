# setup.py (in C:\projects\appserver\base\type_system)
from setuptools import setup, find_packages

setup(
    name="type_system",  # The name of your package
    version="0.1.0",     # Your package's version number
    packages=find_packages(), # Automatically find packages in the directory
    install_requires=[
        # List your dependencies here (if any)
    ],
    # Optional metadata (but good to include)
    author="Your Name",
    author_email="your.email@example.com",
    description="A model-based type system",
    long_description=open("README.md").read(), # Use your README content
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/type_system", # Project URL (if any)
    classifiers=[
        # Choose classifiers from https://pypi.org/classifiers/
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7', # Minimum Python version
)