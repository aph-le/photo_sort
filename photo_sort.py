"""
photo_sort.py
A photo file sorting script.

author: Alexander Philipp

$Id$

"""
import hashlib
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime as Datetime
from dataclasses import dataclass, field
from PIL import Image
from PIL.ExifTags import TAGS
from alive_progress import alive_bar as progress_bar

_LOGGER = logging.getLogger(__name__)

@dataclass
class PhotoSortConfig:
    """Class to hold the configuration and lambdas."""

    src_root_path: Path = Path(".").absolute()
    dst_root_path: Path = Path(".").absolute()
    duplicates_path: Path = Path("./duplicates")
    file_rename_format: str = "%Y-%m-%d_%H-%M-%S"
    file_type_list: list = field(default_factory=lambda: [".jpg", ".jpeg", ".JPG"])
    copy_func: object = lambda file_in, file_out: shutil.copy2(file_in, file_out)


def parse_arguments() -> PhotoSortConfig:
    """Parse command line option and return cofig dataclass."""
    parser = argparse.ArgumentParser()
    parser.add_argument("src_root_dir", type=str, help="source root directory")
    parser.add_argument("dst_root_dir", type=str, help="destination root directory")
    parser.add_argument(
        "-c",
        "--copy",
        action="store_true",
        default=False,
        help="uses copy instead move for files",
    )
    parser.add_argument(
        "-d",
        "--duplicates-folder",
        type=str,
        default="duplicates",
        help="alternative folder name to save duplicate pictures in destination root",
    )
    parser.add_argument(
        "-r",
        "--rename-format",
        type=str,
        default="%Y-%m-%d_%H-%M-%S",
        help="format secifier for renaming the file, see python datetime",
    )
    args = parser.parse_args()

    photo_sort_config = PhotoSortConfig()
    photo_sort_config.src_root_path = Path(args.src_root_dir).absolute()
    photo_sort_config.dst_root_path = Path(args.dst_root_dir).absolute()
    photo_sort_config.duplicates_path = (
        photo_sort_config.dst_root_path / args.duplicates_folder
    )
    photo_sort_config.file_rename_format = args.rename_format

    if args.copy is False:
        photo_sort_config.copy_func = lambda file_in, file_out: shutil.move(
            file_in, file_out
        )

    return photo_sort_config


def parse_exif_date(date_str: str) -> Datetime:
    """Parses the given string to create and return a datetime element.

    :param str date_str: contains descrition of date and time
    """
    # todo check for diffrent input strings
    date_obj = Datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")

    return date_obj


def safe_copy(config: PhotoSortConfig, src_file: str, dest_file: str):
    """Copy or Move file safely by checking if destination file exist and append -X if case
    is already exists.

    :param PhotoSortConfig config: Config which contains the actual copy method.
    :param str src_file: source including complete path.
    :param str dst_file: desired destination file name.
    """
    dest_file_path = Path(dest_file)
    dest_file_dir = dest_file_path.parent
    if not dest_file_path.exists():
        config.copy_func(src_file, dest_file)
    else:
        dest_file_dir = dest_file_path.parent
        dest_file_ext = dest_file_path.suffix
        dest_file_base = dest_file_path.stem
        dest_file_add = 1
        while Path.joinpath(dest_file_dir, f"{dest_file_base}({dest_file_add}){dest_file_ext}").exists():
            dest_file_add = dest_file_add + 1
        dest_file_path = Path.joinpath(dest_file_dir, f"{dest_file_base}({dest_file_add}){dest_file_ext}")
        config.copy_func(src_file, str(dest_file_path))


def get_exif(file_name: str) -> dict:
    """
    Get the image file exif information as dictionary.

    :param str file_name: image file to get the exif data
    :return dict: dictionary with exif tags
    """
    exif_dict = {}
    image = Image.open(file_name)
    info = image.getexif()
    if info is None:
        return {}
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        exif_dict[decoded] = value
    return exif_dict


def create_pic_folder(config: PhotoSortConfig, date: Datetime) -> str:
    """
    Create folder structure if not existing.

    :param PhotoSortConfig config:
    :param Datetime date:
    :return str:
    """
    new_path = f"{date.year}/{date.strftime('%Y_%m')}"
    new_path = config.dst_root_path / new_path

    if new_path.exists() is False:
        new_path.mkdir(parents=True)

    if config.duplicates_path.exists() is False:
        config.duplicates_path.mkdir(parents=True)

    return str(new_path)


def create_pic_name(config: PhotoSortConfig, file_name: str, date: Datetime) -> str:
    """Create a filename for the copy file according to the configuration.

    :param PhotoSortConfig config: Config which contains the actual copy method.
    :param str file_name: old file name include full path
    :param datetime date: date as base element for the new name
    """
    file_name_path = Path(file_name)
    file_path = file_name_path.parent
    file_ext = file_name_path.suffix

    new_name = date.strftime(config.file_rename_format)
    file_renamed = str(Path.joinpath(file_path, f"{new_name}{file_ext}"))

    return file_renamed


def check_unique_file(config: PhotoSortConfig, file, dir) -> str:
    """Create a hashlist from the working directory a see if the file is already in the hashlist."""
    if not hasattr(check_unique_file, "unique_" + dir):
        setattr(check_unique_file, "unique_" + dir, dict())
        unique = getattr(check_unique_file, "unique_" + dir)
        for path in Path(dir).rglob("*"):
            if path.is_file() is True and path.suffix in config.file_type_list:
                filehash = hashlib.md5(open(str(path), "rb").read()).hexdigest()
                if filehash not in unique:
                    unique[filehash] = str(path.name)
                    setattr(check_unique_file, "unique_" + dir, unique)
    unique = getattr(check_unique_file, "unique_" + dir)
    filehash = hashlib.md5(open(file, "rb").read()).hexdigest()
    if filehash not in unique:
        filename = str(Path(file).name)
        unique[filehash] = filename
        setattr(check_unique_file, "unique_" + dir, unique)
        return dir + "/" + filename

    return str(config.duplicates_path / Path(file).name)


def main():
    """Main function"""
    config = parse_arguments()

    root_path = config.src_root_path
    _LOGGER.info("Root Path: " + str(root_path))

    with progress_bar(len(list(root_path.rglob("*")))) as prog_bar:
        for path in root_path.rglob("*"):
            if path.is_file() is True and path.suffix in config.file_type_list:
                filename = str(path)
                prog_bar.text(f"Item: {filename}")
                picture_meta_dict = get_exif(filename)
                picture_date_time = ""
                if "DateTime" in picture_meta_dict:
                    picture_date_time = picture_meta_dict["DateTime"]
                elif "DateTimeOriginal" in picture_meta_dict:
                    picture_date_time = picture_meta_dict["DateTimeOriginal"]
                else:
                    pass
                if picture_date_time != "":
                    date_time = parse_exif_date(picture_date_time)
                    dest_dir = create_pic_folder(config, date_time)
                    new_file = check_unique_file(config, filename, dest_dir)
                    new_file = create_pic_name(config, new_file, date_time)
                    if "" != new_file:
                        safe_copy(config, filename, new_file)
            prog_bar()


if __name__ == "__main__":
    #logging.basicConfig(level=logging.INFO)
    #logger = logging.getLogger("alive_progress")
    main()
