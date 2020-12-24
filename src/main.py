import argparse
import glob
import os
import time
from multiprocessing import Pool
from pprint import pprint

import imagehash
from dotenv import load_dotenv
from PIL import Image

from db import Database

load_dotenv(verbose=True)

class GuyaEye:

    def __init__(self, **kwargs):
        self.kwargs = kwargs

        self.images = self.kwargs['images']
        self.compare = self.kwargs['compare']
        self.threads = self.kwargs['threads']
        self.recursive = self.kwargs['recursive']
        self.include_extensions = (
            self.kwargs["include_extensions"].split(",")
            if self.kwargs["include_extensions"]
            else False
        )
        self.exclude_extensions = (
            self.kwargs["exclude_extensions"].split(",")
            if self.kwargs["exclude_extensions"]
            else False
        )

        if self.images:
            self.create_database()
        elif self.compare:
            self.compare_image()
        else:
            print('[ ERROR ] Please select either "python src/main.py --images <directory>" or python src/main.py --compare <image>"!')

    def create_database(self):
        s = time.time()
        image_files = []
        for image_file in glob.iglob(self.images + "/**", recursive=self.recursive):
            if not os.path.isfile(image_file):
                continue
            elif self.include_extensions and not any(
                image_file.endswith(ext) for ext in self.include_extensions
            ):
                continue
            elif self.exclude_extensions and any(
                image_file.endswith(ext) for ext in self.exclude_extensions
            ):
                continue
            image_files.append(os.path.abspath(os.path.join(self.images, image_file)))
        pool = Pool(self.threads)

        hashes = pool.map(self.hash_image, image_files)

        self.db = Database()
        self.db.truncate()
        for hash in hashes:
            img, h = hash
            self.db.store_encoding(img, h)
        e = time.time()
        print(f'[ OK ] Took {e - s:,.2f} seconds, {(e -s ) / len(hashes):,.2f} sec/image')
    
    def compare_image(self):
        """
            Returns a list of a maximum of 10 images where from lowest distance to maximum distance, with the lowest distance being the closest match.
            A distance of 0 is an exact match.
        """
        self.db = Database()
        _, h = self.hash_image(self.compare)
        res = self.db.compare_encoding(h)
        pprint(res)

    @staticmethod
    def hash_image(image):
        img = Image.open(image)
        return (image, imagehash.average_hash(img, hash_size=16))

    @staticmethod
    def compare_hash(h1, h2):
        return abs(h1 - h2)

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument('--images', type=str, default=False, help='Load directory of images into a database')
    args.add_argument('--compare', type=str, default=False, help='Compare image to the database')
    args.add_argument('--threads', type=int, default=4, help='Number of threads to use when generating the database')
    args.add_argument('--recursive', action="store_true", default=False, help='Recursively search specified images directory when loading to database')
    args.add_argument('--include-extensions', type=str, default=False, help='Comma separated list of extensions that should be filtered for when searching for images')
    args.add_argument('--exclude-extensions', type=str, default=False, help='Comma separated list of extensions that should be filtered out when searching for images')
    args = args.parse_args()

    GuyaEye(**vars(args))