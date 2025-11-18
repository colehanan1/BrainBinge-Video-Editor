"""
HeyGen Social Clipper - Setup Configuration
Transform HeyGen AI videos into viral social media content automatically
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_file(filename):
    """Read file contents."""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

# Version will be defined after initial implementation
VERSION = '0.1.0-alpha'

# Read requirements from requirements.txt
def read_requirements():
    """Parse requirements from requirements.txt."""
    requirements = []
    req_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

setup(
    # Package Metadata
    name='heygen-social-clipper',
    version=VERSION,
    description='Transform HeyGen AI videos into viral social media content',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',

    # Author Information
    author='BrainBinge',
    author_email='support@brainbinge.com',

    # URLs
    url='https://github.com/yourusername/heygen-social-clipper',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/heygen-social-clipper/issues',
        'Source': 'https://github.com/yourusername/heygen-social-clipper',
        'Documentation': 'https://github.com/yourusername/heygen-social-clipper/blob/main/README.md',
    },

    # License
    license='MIT',

    # Python Version Requirement
    python_requires='>=3.10,<3.13',

    # Package Discovery
    packages=find_packages(where='src'),
    package_dir={'': 'src'},

    # Dependencies
    install_requires=read_requirements(),

    # Optional Dependencies
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'pytest-mock>=3.11.1',
            'black>=23.7.0',
            'flake8>=6.1.0',
            'mypy>=1.5.0',
            'isort>=5.12.0',
        ],
        'whisper': [
            'openai-whisper>=20230314',
        ],
        'cloud': [
            'boto3>=1.28.0',  # AWS S3
            'google-cloud-storage>=2.10.0',  # Google Cloud Storage
        ],
        'monitoring': [
            'prometheus-client>=0.17.0',
            'sentry-sdk>=1.30.0',
        ],
    },

    # Entry Points (CLI Commands)
    entry_points={
        'console_scripts': [
            'heygen-clipper=src.cli:main',
        ],
    },

    # Package Data
    include_package_data=True,
    package_data={
        '': [
            'templates/*.yaml',
            'templates/*.json',
        ],
    },

    # Classifiers
    classifiers=[
        # Development Status
        'Development Status :: 3 - Alpha',

        # Intended Audience
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',

        # Topic
        'Topic :: Multimedia :: Video',
        'Topic :: Multimedia :: Video :: Conversion',

        # Python Versions
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',

        # Operating Systems
        'Operating System :: OS Independent',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',

        # Environment
        'Environment :: Console',

        # Natural Language
        'Natural Language :: English',
    ],

    # Keywords
    keywords='video processing heygen social-media automation tiktok instagram youtube-shorts',

    # Zip Safety
    zip_safe=False,
)
