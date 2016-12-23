from setuptools import setup


setup(
    name='evernote_exporter',
    version='0.5dev',
    description='Exports all Evernote notes, notebooks, and stacks in a more widely importable format',
    long_description=open('README.md').read(),
    author='Shawn Daniel',
    author_email='shawndaniel@protonmail.com',
    url='https://github.com/shawndaniel',
    license='GPLv3',
    requires=['html2text'],
)