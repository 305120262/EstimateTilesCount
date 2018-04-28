# Import system modules
import arcpy, sys, math, os
from datetime import datetime
import time
from xml.dom.minidom import parse, parseString

#########################Variables################################
# Enter the location to your feature class that contains the features
# you wish to cache by.
# cacheFeatures = "C:/serverblog/blogCacheTest/personal.mdb/county"
# cacheFeatures = "C:/serverblog/blogCacheTest/file.gdb/county"
# cacheFeatures = "C:/serverblog/blogCacheTest/county.shp"
cacheFeatures = "D:/DemoDatas/CantonMap/Shp/admin.gdb/boder_p"

# Enter the cache configuration file (conf.xml) for your cached map service.
# This will give you and estimate on how many tiles will be generated for each extent
# cacheConfig = parse('C:/arcgisserver/arcgiscache/mapservice/Layers/conf.xml')
cacheConfig = parse('C:/Program Files/ArcGIS/Server/TilingSchemes/ArcGIS_Online_Bing_Maps_Google_Maps.xml')

# Enter the name of your ArcGIS Server
server_name = "seanpc"

# Enter the name of your predefined Cached Service
# If your service is in a folder then the syntax is: foldername/servicename
# If a service USAMap was in the basemap folder the syntax would be:
# service_name = "basemap/USAMap"
service_name = "SampleWorldCities"

# Enter the name of your predefined cached map dataframe
data_frame = "Layers"

# Enter the layers you wish to cache, leave blank to cache all layers
layers = ""
# layers = "ushigh;counties;states"

# Enter scales you wish to cache.  These should be similar to the scales
# that you have already cached your service at.
scales = "16000000;8000000;4000000;2000000;1000000;500000;250000;125000;64000;32000;16000;5000;2500;1200;600;300;150"

# Enter update mode.  Recreate All Tiles, replaces all tiles.
# Recreate Empty Tiles, replaces only empty tiles.
update_mode = "Recreate All Tiles"

# Enter the number of SOCs that you wish to cache with
# This can be no more than the max set for the service.
thread_count = "2"

# Whether you want to use Antialiasing or not.
antialiasing = "ANTIALIASING"


# antialiasing = "NONE"
#########################Variables################################

# Use to get text from XMLDom of cache configuration file
def getText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc


# function that parsed cache configuration xml file and an extent and computes the
# number of rows and columns that should have been computed for each scale within
# the update extent.
def handleTileCacheInfo(tilecacheinfo, extent):
    MinX = extent.XMin
    MinY = extent.YMin
    MaxX = extent.XMax
    MaxY = extent.YMax
    TileRows = int(getText(tilecacheinfo.getElementsByTagName("TileRows")[0].childNodes))
    TileCols = int(getText(tilecacheinfo.getElementsByTagName("TileCols")[0].childNodes))
    TileOrigin = tilecacheinfo.getElementsByTagName("TileOrigin")[0]
    TileOriginX = float(getText(TileOrigin.getElementsByTagName("X")[0].childNodes))
    TileOriginY = float(getText(TileOrigin.getElementsByTagName("Y")[0].childNodes))
    DPI = int(getText(tilecacheinfo.getElementsByTagName("DPI")[0].childNodes))

    LODInfos = tilecacheinfo.getElementsByTagName("LODInfos")[0]

    totalTiles = 0
    for lodinfo in LODInfos.childNodes:
        LevelID = getText(lodinfo.getElementsByTagName("LevelID")[0].childNodes)
        Scale = getText(lodinfo.getElementsByTagName("Scale")[0].childNodes)
        Resolution = float(getText(lodinfo.getElementsByTagName("Resolution")[0].childNodes))

        ## Compute number of tiles wide.
        tileWidth = TileCols * Resolution
        tileColumn = math.floor((MinX - TileOriginX) / tileWidth)
        tileColumn_End = math.floor((MaxX - TileOriginX) / tileWidth)
        numTilesWideFromTile = tileColumn_End - tileColumn +1
        print "LevelID= " + str(LevelID)
        print "Scale= " + str(Scale)
        print "Resolution= " + str(Resolution)
        print "numTilesWideFromTile = " + str(numTilesWideFromTile)

        ## Compute number of tiles high.
        tileHeight = TileRows * Resolution
        tileRow = math.floor((TileOriginY - MinY) / tileHeight)
        tileRow_End = math.floor((TileOriginY - MaxY) / tileHeight)
        numTilesHighFromTile =   tileRow - tileRow_End +1
        print "numTilesHighFromTile = " + str(numTilesHighFromTile)
        print "totalTiles= " + str(numTilesWideFromTile * numTilesHighFromTile)
        totalTiles += numTilesWideFromTile * numTilesHighFromTile
        print ""

    return totalTiles


# check input featureclass to see if the "Cached" field exists.  If it exists then
# proceed.  If it does not then add "Cached" field to the feature class
# if arcpy.ListFields(cacheFeatures,"CACHED").Next():
# print "field Cached exists"
# else:
# print "field does not exist"
# arcpy.addfield (cacheFeatures, "CACHED", "TEXT")

# Describe featureClass and get the shape field name.
desc = arcpy.Describe(cacheFeatures)
shapefieldname = desc.ShapeFieldName

# Create an update cursor on the featureclass for all features where the Cached field
# has not been set to 'yes'.
# if desc.DataType == "ShapeFile":
# qString = '"CACHED" <> ' + "'yes'"
# else:
# if cacheFeatures.find('.mdb') > 0:
# qString = '[CACHED] IS NULL'
# else:
# qString = '"CACHED" IS NULL'

with arcpy.da.SearchCursor(cacheFeatures, "SHAPE@") as rows:
    # While row is not empty (until all features have been processed) get the feature for
    # the current row and use the getFeatureExtent function to get the feature extent.  Use
    # the feature extent to call updateMapServerCache for the predefined scales and
    # cache parameters.  If the cache finishes successfully then update the featureclass
    # so that the Cached field reads 'true'.  If it does not finish successfully then the
    # script will stop.  You can rerun the script with the current featureclass and it
    # pick up at the row it left off at.
    for row in rows:
        feat = row[0]
        constraining_extent = feat.extent
        #print "Updating envelope: " + str(row.GetValue(desc.OIDFieldName))
        print constraining_extent
        try:
            startTime = datetime.now()
            # arcpy.UpdateMapServerCache(server_name, service_name, data_frame, layers, constraining_extent, scales, update_mode, thread_count, antialiasing)
            # arcpy.UpdateMapServerCache_server(server_name, object_name, data_frame, layers, constraining_extent, scales, update_mode, thread_count, antialiasing)
            # print arcpy.GetMessages(1)
            # row.CACHED = "yes"
            # rows.UpdateRow(row)
            # endTime = datetime.now()
            # time_difference = endTime-startTime
            tileCount = handleTileCacheInfo(cacheConfig, constraining_extent)
            print "Total tiles generated for this extent: " + str(tileCount)
            # print 'elapsed', time_difference
            # print "Tiles generated per minute: " + str(tileCount/(time_difference.seconds / 60.0))
            print "Finished env update."
            print ""
        except:
            arcpy.AddMessage(arcpy.GetMessages(2))
            print arcpy.GetMessages(2)
            print "update failed, stop processing"
            del rows
            del arcpy
            sys.exit(1)


print "Update Complete"