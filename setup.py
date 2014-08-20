from setuptools import setup

setup(name='fealden',
	version='0.1',
	description='Fealden is a tool for the automated creation of tTranscription factor beacons, novel biosensor probes for transcription factor activity and quantity.',
	url='http://github.com/jodys/fealden',
	author='Jody Stephens',
	author_email='jody.stephens@gmail.com',
	license='MIT',
	packages=['fealden', 'web'],
	install_requires=[
		'setproctitle',
		'python-daemon',
		'web.py',
		'numpy',
		'matplotlib'],
	scripts = ['bin/fealdend'],
	include_package_data = True,
#	package_data = {
#		'web':['templates/*.html'],
#		'fealden':[]},
	test_suite='nose.collector',
	tests_require=['nose'],
	zip_safe=False)

