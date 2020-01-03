from distutils.core import setup
version = '1.0.1'

setup(
  name = 'moneydashboard',
  packages = ['moneydashboard'], # this must be the same as the name above
  version = version,
  description = 'MoneyDashboard library for accessing its API',
  author = 'Martin Brooksbank',
  author_email = 'martin@flamedevelopment.co.uk',
  url = 'https://github.com/shutupflandrs/moneydashboard',
  download_url = 'https://github.com/shutupflandrs/moneydashboard/tarball/{0}'.format(version),
  keywords = ['money dashboard', 'financial', 'money'],
  classifiers = [],
)