""" Packaging of PagerMaid. """

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()
with open("requirements.txt", "r") as fp:
    install_requires = fp.read()

setup(
    name="pagermaid_modify",
    version="2020.8.post1",
    author="xtaodada",
    author_email="xtao@xtaolink.cn",
    description="A telegram utility daemon and plugin framework.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xtaodada/PagerMaid-Modify",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'pagermaid=pagermaid:__main__'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: Unix"
    ],
    python_requires=">=3.6",
    install_requires=install_requires,
    include_package_data=True
)
