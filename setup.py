import setuptools
setuptools.setup(
    version='0.0.1',

    author='Yuval',
    author_email='yuvalino@gmail.com',

    name='clex',
    description='C lexical analysis',

    url='https://github.com/yuvalino/python-clex',
    project_urls={
        'Source Code': 'https://github.com/yuvalino/python-clex'
    },

    install_requires=['six'],

    package_data={'': [
        '*.txt',
        '*.rst'
    ]},

    classifiers=[
        'Programming Language :: Python',
    ],

    packages=setuptools.find_packages(),
)