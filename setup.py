import os
import sys
from setuptools import setup, find_packages
from tethys_apps.app_installation import custom_develop_command, custom_install_command

# ### Apps Definition ###
app_package = 'hydroshare_gis'
release_package = 'tethysapp-' + app_package
app_class = 'hydroshare_gis.app:HydroshareGis'
app_package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tethysapp', app_package)

# ### Python Dependencies ###
dependencies = ['hs-restclient', 'rasterio', 'fiona', 'numpy', 'os']

setup(
    name='HydroShare GIS',
    version='2.0',
    description='View HydroShare Raster and Feature Resources and/or upload them from your computer.',
    long_description='',
    keywords='',
    author='Kenneth Lippold',
    author_email='klippold@byu.net',
    url='',
    license='The MIT License (MIT)',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['tethysapp', 'tethysapp.' + app_package],
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
    cmdclass={
        'install': custom_install_command(app_package, app_package_dir, dependencies),
        'develop': custom_develop_command(app_package, app_package_dir, dependencies)
    }
)
