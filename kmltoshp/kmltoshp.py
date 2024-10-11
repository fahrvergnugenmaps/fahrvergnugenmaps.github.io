import geopandas as gpd
import sys
from datetime import datetime

kml_file = "sys.argv[0]"
gdf = gpd.read_file(kml_file)

shapefile_path = "/Users/tom/Documents/GitHub/fahrvergnugenmaps.github.io/kmltoshp/shapefile.shp"
gdf.to_file(shapefile_path, driver="ESRI Shapefile")