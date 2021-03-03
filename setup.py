from setuptools import setup

with open('README.md', encoding='utf-8') as f:
    long_description = f.read().replace('\r\n', '\n')

setup(
    name = 'just_playback',       
    packages = ['just_playback'],   
    version = '0.1',      
    author = 'Cheo Fusi',                  
    author_email = 'fusibrandon13@gmail.com',
    url = 'https://github.com/cheofusi/just_playback', 
    description = 'A small package for playing audio in python \
                    with file format independent methods for playback control', 
    long_description = long_description,
    long_description_content_type='text/markdown',
    license='MIT',   
    keywords = [    
        'audio',  
        'music',
        'wave',
        'wav'
        'mp3',
        'media',
        'song',
        'play', 
        'player',
        'playback', 
        'audioplayer', 
        'mp3player'
    ],  
    install_requires=[            
        'numpy',
        'audioread',
        'PyAudio'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',         
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Topic :: Multimedia",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "Topic :: Multimedia :: Sound/Audio :: Players :: MP3",
        'License :: OSI Approved :: MIT License',  
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    )