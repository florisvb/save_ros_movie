from distutils.core import setup

setup(
    name='RosMovieAnalysis',
    version='0.0.1',
    author='Floris van Breugel',
    author_email='floris@caltech.edu',
    packages = ['ros_movie_analysis'],
    license='BSD',
    description='code for opening and reading data created with save_ros_movie',
    long_description=open('README.txt').read(),
)



