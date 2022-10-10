from setuptools import setup

setup(
    name='django_verification',
    version='0.0.1',
    author='Shaghayegh Ghorbanpoor',
    author_email='ghorbanpoor.shaghayegh@gmail.com',
    packages=['django_verification'],
    # scripts=['bin/script1', 'bin/script2'],
    # url='http://pypi.python.org/pypi/PackageName/',
    # license='LICENSE.txt',
    description='An awesome package that create verification views',
    # long_description=open('README.md').read(),
    install_requires=[
        'Django',
        'redis',
        'drf_yasg',
        'django_validation@git+https://github.com/shaqayegh-gh/django_validation.git',
    ],
)
