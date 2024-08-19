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

def calc_new_tuple(input_tuple, offset_to, above_below):
    """
    :param input_tuple: tuple from exif
    :param offset_to: offset value
    """
    numerator = input_tuple[0]
    denominator = input_tuple[1]
    if above_below == 0:
        num_div_den = numerator / denominator
    else:
        num_div_den = -(numerator / denominator)

    new_alt = num_div_den + offset_to

#    print(num_div_den)
#    print(normalized_offset)
    print(new_alt)
#    print(numerator)
#    print(denominator)


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

        #width, height = im.size
        #max_side = max(width, height)

        #if isinstance(refine_to, str) and refine_to.endswith("%"):
        #    ratio = float(refine_to[:-1]) / 100.0
        #else:
        #    ratio = float(refine_to) / float(max_side)

        #refined_width = int(width * ratio)
        #refined_height = int(height * ratio)

        #im.thumbnail((refined_width, refined_height), Image.LANCZOS)

        driver = ext[1:].upper()
        if driver == 'JPG':
            driver = 'JPEG'

        if 'exif' in im.info:
            exif_dict = piexif.load(im.info['exif'])
#            for ifd_name in exif_dict:
#                print("\n{0} IFD:".format(ifd_name))
#                for key in exif_dict[ifd_name]:
#                    try:
#                        print(key, exif_dict[ifd_name][key][:10])
#                    except:
#                        print(key, exif_dict[ifd_name][key])

            #print((exif_dict['GPS'][piexif.GPSIFD.GPSAltitude])[0])
            altitude_tuple = exif_dict['GPS'][piexif.GPSIFD.GPSAltitude]
            above_below = exif_dict['GPS'][piexif.GPSIFD.GPSAltitudeRef]
            calc_new_tuple(altitude_tuple, 5, above_below)
            exif_dict['GPS'][piexif.GPSIFD.GPSAltitude] = (5377, 1000)
            im.save(refined_image_path, driver, exif=piexif.dump(exif_dict), quality=100)
        else:
            im.save(refined_image_path, driver, quality=100)

        im.close()

        #print("{} ({}x{}) --> {} ({}x{})".format(image_path, width, height, refined_image_path, refined_width, refined_height))
    except (IOError, ValueError) as e:
        print("Error: Cannot refine {}: {}.".format(image_path, str(e)))
        nonloc.errors += 1


#if not args.amount.endswith("%"):
#    args.amount = float(args.amount)
#    if args.amount <= 0:
#        die("Invalid amount")
#else:
#    try:
#        if float(args.amount[:-1]) <= 0:
#            die("Invalid amount")
#    except:
#        die("Invalid amount")


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

