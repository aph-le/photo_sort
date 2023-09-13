import os, hashlib, shutil, argparse
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from dataclasses import dataclass


@dataclass
class PhotoSortConfig:
    """Class to hold the configuration and lambdas."""
    src_root_path: Path = Path(".").absolute()
    dst_root_path: Path = Path(".").absolute()
    duplicates_path: Path = Path("./duplicates")
    copy_func: object = lambda file_in, file_out: shutil.copy(file_in, file_out)


def parse_arguments() -> PhotoSortConfig:
    """Parse command line option and return cofig dataclass."""
    parser = argparse.ArgumentParser()
    parser.add_argument("src_root_dir", type=str, help="source root directory")
    parser.add_argument("dst_root_dir", type=str, help="destination root directory")
    parser.add_argument("-c", "--copy", action="store_true", default=False, help="uses copy instead move for files")
    parser.add_argument("-d", "--duplicates-folder", type=str, default="duplicates", help="alternative folder name to save duplicate pictures in destination root")
    args = parser.parse_args()

    photo_sort_config = PhotoSortConfig()
    photo_sort_config.src_root_path = Path(args.src_root_dir).absolute()
    photo_sort_config.dst_root_path = Path(args.dst_root_dir).absolute()
    photo_sort_config.duplicates_path = photo_sort_config.dst_root_path / args.duplicates_folder


    if args.copy == True:
        photo_sort_config.copy_func = lambda file_in, file_out: shutil.copy(file_in, file_out)
    else:
        photo_sort_config.copy_func = lambda file_in, file_out: shutil.move(file_in, file_out)

    return photo_sort_config


def get_exif(file_name) -> dict:
    """Get the image file exif information as dictionary."""
    exif_dict = {}
    image = Image.open(file_name)
    info = image.getexif()
    if info == None:
        return dict()
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        exif_dict[decoded] = value
    return exif_dict


def create_pic_folder(date):
    """Create folder structure if not existing."""
    year = date.split(':')[0]
    month = date.split(':')[1]
    if not os.path.isdir("duplicates"):
        os.mkdir("duplicates")
    if not os.path.isdir(year):
        os.mkdir(year)
    if not os.path.isdir(year + '/' + month):
        os.mkdir(year + '/' + month)
    return year + '/' + month


def check_unique_file(file, dir):
    """Create a hashlist from the working directory a see if the file is already in the hashlist."""
    unique = dict()
    print(os.listdir(dir))
    for filename in os.listdir(dir):
        print(dir + '/../' +filename)
        if os.path.isfile('./' + dir + '/' + filename):
            print(dir + '/++/' +filename)
            if '.jpg' in filename:
                filehash = hashlib.md5(open('./' + dir + '/' + filename, 'rb').read()).hexdigest()
                if filehash not in unique:
                    print('not in hashtable ' + filename)
                    unique[filehash] = filename
            else:
                # should never happen
                return ''
    print(unique)
    filehash = hashlib.md5(open(file, 'rb').read()).hexdigest()
    if filehash not in unique:
        print('------ not in hashtable ' + file)
        filename = str(Path(file).name)
        return dir + '/' + filename
    else:
        print(filename + ' is a duplicate in folder ' + unique[filehash])
        return 'duplicates/' + filename


def main():
    cmd_options = parse_arguments()

    root_path = cmd_options.src_root_path 
    print('Root Path: ' + str(root_path))

    for path in root_path.rglob("*"):
        if path.is_file() == True and path.suffix == ".jpg":
            filename = str(path)
            print(filename)
            picture_meta_dict = get_exif(filename)
            picture_date_time = ""
            if 'DateTime' in picture_meta_dict:
                picture_date_time = picture_meta_dict['DateTime']
            if 'DateTimeOriginal' in picture_meta_dict:
                picture_date_time = picture_meta_dict['DateTimeOriginal']
            else:
                pass
            if picture_date_time != "":
                dest_dir = create_pic_folder(picture_date_time)
                new_file = check_unique_file(filename, dest_dir)
                if '' != new_file:
                    cmd_options.copy_func(filename, new_file)


if __name__ == '__main__':
    main()

