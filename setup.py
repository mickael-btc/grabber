from setuptools import setup

setup(
    name='grabber',
    version='0.9',
    description='A cross-platform package to make screenshots from any winwdow',
    author='Mickael Bobovitch',
    author_email='m.bobovitch@gmail.com',
    url='https://github.com/mickael-btc/grabber',
    license="MIT",
    packages=['grabber'],
    install_requires=['opencv-python', 'numpy'],
)        