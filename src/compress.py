"""
This scripts assumes that all input tiff files that semantically belong to one 'DATASET' are in the same folder.
It will compress the geotiffs into JPEG compressed tiffs, move all processed files into a 'raw' folder and
save the compressed files into a 'compressed' folder. Metadata about the compressin is saved into a json, that
is not overwritten.

The output json will look as follows:
{
    "dataset": "DATASET",
    "files": [
        {
            "filename": "FILENAME",
            "compression": "JPEG",
            "quality": 60
            ...
        }
    ]
}

"""
from pathlib import Path
import click
import json
import glob
import shutil

from osgeo import gdal


@click.command()
@click.option("--quality", default=None, type=int, help="JPEG quality factor. 0 is worst, 100 is best.")
@click.option("--scaling", default=None, type=float, help="Scaling factor for the output image. 0.5 means half the number of pixels in each direction.") 
@click.option("--mem-limit", default=1024, type=int, help="Maximum memory limit for GDAL in MB.")
@click.option("--quiet", default=False, is_flag=True, help="Suppress output.")
@click.argument("dataset_path", default="*")
def run_compression(quality, scaling, mem_limit, quiet, dataset_path):
    """"""
    # Here we could load a generic config file, Environment variables, 
    # anything that gcloud can use to pass in parameters
    # parse the parameters
    if quality is None:
        if not quiet:
            click.echo("No quality factor given, using default value of 75.")
        quality = 75
    if scaling is None:
        if not quiet:
            click.echo("No scaling factor given, using default value of 1.0.")
        scaling = 1.0
    
    # use glob to find all datasets as specified by the user
    # hardcode the /in folder
    datasets = glob.glob(str((Path('/in') / dataset_path).resolve()))
    # only use stuff that is a folder
    datasets = [Path(d) for d in datasets if Path(d).is_dir()]
    
    if not quiet:
        click.echo(f"Found {len(datasets)} datasets to process.")
    
    for dataset in datasets:
        # find all tiffs in the dataset folder
        tiffs = glob.glob(str(dataset / "*.tif"))

        if not quiet:
            click.echo(f"Comressing {len(tiffs)} GeoTIFF in {str(dataset.name)}.")
        
        # if there is more than one, we will need a raw folder
        raw_folder = dataset / "raw"
        if len(tiffs) > 1 and not raw_folder.exists():
            raw_folder.mkdir(parents=True, exist_ok=True)
        
        # main loop
        for filename in tiffs:
            if not quiet:
                click.echo(f"Compressing {filename}...")
            # compress the file
            compressed_file = compress_geotiff(filename, scaling=scaling, quality=quality, maxmemory=mem_limit)

            # and update the metadata
            update_metadata(dataset, compressed_file)

            # move original to raw data
            shutil.move(filename, str(raw_folder / Path(filename).name))


def compress_geotiff(
    input_file: str,
    output_file: str = None,
    scaling: float = 1.0,
    quality: int = 75,
    nodata=["0", "255"],
    maxmemory: int = 4096, 
    force_overwirte: bool = False
) -> Path:
    """"""
    # get the absolute path to the file
    tif_file = Path(input_file).resolve()
    
    # create the output file name if not given
    if output_file is None:
        output_file: Path = tif_file.parent / "compressed" / tif_file.name

    # create the output folder if it does not exist
    if not output_file.parent.exists():
        output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # if the output file exists and we are not forced to overwirte, skip
    if not force_overwirte and output_file.exists():
        return output_file

    # open the file in read only mode
    datasource = gdal.Open(str(tif_file), gdal.GA_ReadOnly)

    # create the output file
    # gdalwarp -r cubic -ts 2551 0  -wm 2048 -multi -wo NUM_THREADS=ALL_CPUS -co NUM_THREADS=ALL_CPU -co COMPRESS=JPEG -co JPEG_QUALITY=60 uavforsat_2017_CFB005_ortho.tif compressed/warptest.tif
    options = f"-r cubic -ts {int(datasource.RasterXSize * scaling)} 0 -srcnodata {' '.join(nodata)} -wm {maxmemory} -multi -wo NUM_THREADS=ALL_CPUS -co NUM_THREADS=ALL_CPUS -co COMPRESS=JPEG -co JPEG_QUALITY={quality}"
    gdal.Warp(str(output_file), datasource, callback=gdal.TermProgress_nocb, options=options)

    # garbage collect the references to close and save
    datasource = None

    # return the file path of the created compressed file
    return output_file


def update_metadata(dataset_path: Path, processed_file: Path):
    """
    Create or add metadata to an existing metadata file for a dataset-
    """
    # resolve the dataset path
    dataset_path = Path(dataset_path).resolve()
    dataset = dataset_path.stem
    metadata_file = dataset_path / f"{dataset}.metadata.json"

    # if the metadata file exists, load it
    if metadata_file.exists():
        with open(str(metadata_file), "r") as f:
            metadata = json.load(f)
    else:
        metadata = {"dataset": dataset, "files": []}

    # get existing record if there is one
    filemeta = next((f for f in metadata["files"] if f["filename"] == str(processed_file.name)), {'filename': str(processed_file.name)})
    
    # open the file again
    datasource = gdal.Open(str(processed_file), gdal.GA_ReadOnly)

    meta = gdal.Info(datasource, format='json')

    # update metadata
    filemeta.update(dict(
        driver = meta.get('driverLongName', 'unknown'),
        transform = meta.get('geoTransform', []),
        width = meta.get('size', [])[0],
        height = meta.get('size', [])[1],
        bands = meta.get('bands', []),
        corners = meta.get('cornerCoordinates', {}),
        **{k.lower(): v for k,v in meta.get('metadata',{}).get('IMAGE_STRUCTURE', {}).items()},
    ))

    # garbage collect the references to close and save
    datasource = None

    # set the new filelist
    file_list = [f for f in metadata["files"] if f["filename"] != str(processed_file.name)]
    file_list.append(filemeta)

    # update the metadata
    metadata["files"] = file_list

    # write back
    with open(str(metadata_file), "w") as f:
        json.dump(metadata, f, indent=4)


def cleanup():
    pass


if __name__ == '__main__':
    run_compression()
