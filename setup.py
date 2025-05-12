
from setuptools import setup, find_packages

setup(
    name="code_roast_bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "openai==1.16.2",
        "python-dotenv==1.0.1",
        "tiktoken==0.6.0",
        "tenacity==8.2.3",
        "colorama==0.4.6"
    ],
    entry_points={
        "console_scripts": [
            "code-roast=code_roast_bot.main:main",
        ],
    },
    author="Your Name",
    description="A security-hardened, personality-driven GPT-powered Python code roasting tool.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="BSD-3-Clause",
)
