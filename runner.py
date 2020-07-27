# This script iterates a function from infocrue.py on different scenario.

import glob
import concurrent.futures

import argparse
import json

# local imports
import parallelized_tasks

parser = argparse.ArgumentParser()

parser.add_argument(
    "--function",
    required=True,
    help="Name of the function from parallelized_tasks to call"
)
parser.add_argument(
    "--arguments",
    help="Arguments to the function, as a dictionary json string."
)
parser.add_argument(
    "--files",
    help="Files glob pattern. It will be used with glob.glob to produce the file list."
)
parser.add_argument(
    "--output_dir",
    help="Output directory",
    default="/processing/output/"
)
parser.add_argument(
    "--threads", 
    help="Max number of concurrent processes",
    default=8,
    type=int
)
args = parser.parse_args()

function = getattr(parallelized_tasks, args.function)
kwargs = json.loads(args.arguments)

def main():

    fileList = glob.glob(args.files)
    e = concurrent.futures.ProcessPoolExecutor(max_workers=args.threads)
    for file in fileList:
        e.submit(function, file, **kwargs)
    e.shutdown(wait=True)

if __name__ == '__main__':
    main()
