# PhotoSort
## Description
Python script using exif information from camera pictures to create a folder structure and move pictures into the corresponding folder. The dectection of duplicates is based on md5 hashes. If the script a duplicate file in the destination folder, it will be copied to a special folder (default: duplicates).

## Usage
There is a command line help implemented. For help call:

    python photo_sort.py -h

### Command Line Parameters
    -h --help  : prints command line help 

