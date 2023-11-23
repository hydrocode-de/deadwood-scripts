import os
import glob
import subprocess
from tqdm import tqdm

from osgeo import gdal

# print some header info
cmd = subprocess.run(["gdalinfo", "--version"], capture_output=True, text=True)
print(cmd.stdout)

# get a list of all .tif in the input folder
in_files = glob.glob('/in/*.tif')
print(f"Found {len(in_files)} input tif.")

# initialize a driver
driver = gdal.GetDriverByName('COG')
print('Using GDAL driver:', driver.GetDescription())

# build the COG output args
OUT_ARGS = ["OVERVIEWS=IGNORE_EXISTING", "COMPRESS=JPEG", "QUALITY=60", "BLOCKSIZE=512", "NUM_THREADS=ALL_CPUS", "OVERVIEW_COMPRESS=JPEG", "OVERVIEW_QUALITY=60"]

# main loop to 
for fname in tqdm(in_files):
    # open the file in read only mode
    datasource = gdal.Open(fname, gdal.GA_ReadOnly)

    # create the cog
    out_fname = os.path.join('out', os.path.basename(fname))

    out_cog = driver.CreateCopy(out_fname, datasource, options=OUT_ARGS)
    out_cog = None
    datasource = None

print("Done!")
