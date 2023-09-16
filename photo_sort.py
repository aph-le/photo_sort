import os, hashlib, shutil, argparse
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from dataclasses import dataclass, field


@dataclass
class PhotoSortConfig:
    """Class to hold the configuration and lambdas."""
    src_root_path: Path = Path(".").absolute()
    dst_root_path: Path = Path(".").absolute()
    duplicates_path: Path = Path("./duplicates")
    file_type_list: list = field(default_factory=lambda: [".jpg", ".jpeg"])
    copy_func: object = lambda file_in, file_out: shutil.copy2(file_in, file_out)


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
        photo_sort_config.copy_func = lambda file_in, file_out: shutil.copy2(file_in, file_out)
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


def create_pic_folder(config: PhotoSortConfig, date) -> str:
    """Create folder structure if not existing."""
    year = date.split(':')[0]
    month = date.split(':')[1]

    new_path = f"{year}/{year}_{month}"
    new_path = config.dst_root_path / new_path

    if new_path.exists() == False:
        new_path.mkdir(parents=True)

    if config.duplicates_path.exists() == False:
        config.duplicates_path.mkdir(parents=True)

    return(str(new_path))


def check_unique_file(config: PhotoSortConfig, file, dir) -> str:
    """Create a hashlist from the working directory a see if the file is already in the hashlist."""
    if not hasattr(check_unique_file, "unique_" + dir):
        setattr(check_unique_file, "unique_" + dir, dict())
        unique = getattr(check_unique_file, "unique_" + dir)
        print(os.listdir(dir))
        for path in Path(dir).rglob("*"):
            if path.is_file()  == True and path.suffix in config.file_type_list:
                print(str(path))
                filehash = hashlib.md5(open(str(path),'rb').read()).hexdigest()
                if filehash not in unique:
                    print('not in hashtable ' + str(path.name))
                    unique[filehash] = str(path.name)
                    setattr(check_unique_file, "unique_" + dir, unique)
    unique = getattr(check_unique_file, "unique_" + dir)
    print(unique)
    filehash = hashlib.md5(open(file, 'rb').read()).hexdigest()
    if filehash not in unique:
        print('------ not in hashtable ' + file)
        filename = str(Path(file).name)
        unique[filehash] = filename
        setattr(check_unique_file, "unique_" + dir, unique)
        return dir + '/' + filename
    else:
        print(file + ' is a duplicate in folder ' + unique[filehash])
        return str(config.duplicates_path / Path(file).name)


def main():
    config = parse_arguments()

    root_path = config.src_root_path 
    print('Root Path: ' + str(root_path))

    for path in root_path.rglob("*"):
        if path.is_file() == True and path.suffix in config.file_type_list:
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
                dest_dir = create_pic_folder(config, picture_date_time)
                new_file = check_unique_file(config, filename, dest_dir)
                if "" != new_file:
                    config.copy_func(filename, new_file)


if __name__ == '__main__':
    main()

