import argparse
import os
import glob
import shutil
from PIL import Image
import piexif
import multiprocessing
from multiprocessing.pool import ThreadPool

parser = argparse.ArgumentParser(description='Exif Image Resize')
parser.add_argument('--input', '-i',
                    metavar='<path>',
                    required=True,
                    help='Path to input image or image folder')
parser.add_argument('--output', '-o',
                    metavar='<path>',
                    required=True,
                    help='Path to output image or image folder')
parser.add_argument('--force', '-f',
                    action='store_true',
                    default=False,
                    help='Overwrite results')
parser.add_argument('offset',
                    metavar='<meters>',
                    type=float,
                    help='Amount to add to elevation (negative for subtraction)')
args = parser.parse_args()

def die(msg):
    print(msg)
    exit(1)

class nonloc:
    errors = 0

# Altitude calculator
def altulator(input_tuple, offset_to, above_below):
    """
    :param input_tuple: tuple from exif
    :param offset_to: offset value
    :param offset_to: above sea level flag
    """
    numerator = input_tuple[0]
    denominator = input_tuple[1]
    offset_to_int = round(offset_to * denominator, 0)

    if above_below == 0:
        num = int(numerator)
    else:
        num = int(-numerator)

    new_alt = int(num + offset_to_int)

    if new_alt >= 0:
        is_below = 0
    else:
        is_below = 1

    new_tuple = (abs(new_alt), denominator, is_below)
    return new_tuple
    print(new_tuple) 

def refine_image(image_path, out_path, offset_to, out_path_is_file=False):
    """
    :param image_path: path to the image
    :param out_path: path to the output directory or file
    :param offset_to: Amount to add to elevation (negative for subtraction)
    """
    try:
        im = Image.open(image_path)
        path, ext = os.path.splitext(image_path)
        if out_path_is_file:
            refined_image_path = out_path
        else:
            refined_image_path = os.path.join(out_path, os.path.basename(image_path))

        driver = ext[1:].upper()
        if driver == 'JPG':
            driver = 'JPEG'

        if 'exif' in im.info:
            exif_dict = piexif.load(im.info['exif'])

            # Assign existing altitude tuple and ref to variables
            altitude_tuple = exif_dict['GPS'][piexif.GPSIFD.GPSAltitude]
            above_below = exif_dict['GPS'][piexif.GPSIFD.GPSAltitudeRef]

            # Pass altitude, offset, and ref to altitude calculator
            altituple = altulator(altitude_tuple, offset_to, above_below)
            new_tuple = (abs(altituple[0]), altituple[1])
            exif_dict['GPS'][piexif.GPSIFD.GPSAltitude] = new_tuple
            exif_dict['GPS'][piexif.GPSIFD.GPSAltitudeRef] = altituple[2]
            print("Calculated new altitude for", refined_image_path)
            im.save(refined_image_path, driver, exif=piexif.dump(exif_dict), quality=100)
        else:
            im.save(refined_image_path, driver, quality=100)

        im.close()

    except (IOError, ValueError) as e:
        print("Error: Cannot refine {}: {}.".format(image_path, str(e)))
        nonloc.errors += 1

files = []
if os.path.isdir(args.input):
    for ext in ["JPG", "JPEG", "PNG", "TIFF", "TIF"]:
        files += glob.glob("{}/*.{}".format(args.input, ext))
        files += glob.glob("{}/*.{}".format(args.input, ext.lower()))
elif os.path.exists(args.input):
    files = [args.input]
else:
    die("{} does not exist".format(args.input))

create_dir = len(files) > 1 or args.output.endswith("/")

if create_dir and os.path.isdir(args.output):
    if not args.force:
        die("{} exists, pass --force to overwrite results")
    else:
        shutil.rmtree(args.output)
elif not create_dir and os.path.isfile(args.output):
    if not args.force:
        die("{} exists, pass --force to overwrite results")
    else:
        os.remove(args.output)

if create_dir:
    os.makedirs(args.output)

pool = ThreadPool(processes=multiprocessing.cpu_count())

def refine(file):
    return refine_image(file, args.output, args.offset, not create_dir)
pool.map(refine, files)

print("Process completed, {} errors.".format(nonloc.errors))

