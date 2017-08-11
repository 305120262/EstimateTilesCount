#########################Description#####################################  
#The script I have written allows you to update an existing cache using a feature class
#whose features represent the areas you wish to cache (a regularly spaced grid or other
#features of interest). Within the script itself you identify the location of the feature
#class (needs to be in the same projection as your map service), the location of the
#cache configuration file, and the specific update cache parameters for your cached map
#service (server name, service name, data frame name, scales to cache, update mode, &
#whether or not to use anti-aliasing).  
#
#When executed, the script will check the feature class to see if the "Cached" field
#exists.  If it does not exist it will create the column and run update map server cache
#for each feature.  When the update procedure for that feature finishes it will mark that
#feature as cached and move to the next feature.  If the "Cached" field does exist, it
#will skip the features that have already been marked as having been cached and start
#up where it left off.
#Please send questions to Jeremy Bartley jbartley@esri.com
#########################Description#####################################  

# Import system modules
import arcpy, sys, math, os
from datetime import datetime
import time
from xml.dom.minidom import parse, parseString

#########################Variables################################
#Enter the location to your feature class that contains the features
#you wish to cache by.
#cacheFeatures = "C:/serverblog/blogCacheTest/personal.mdb/county"
#cacheFeatures = "C:/serverblog/blogCacheTest/file.gdb/county"
#cacheFeatures = "C:/serverblog/blogCacheTest/county.shp"
cacheFeatures = "D:/DemoDatas/ChinaProvince.gdb/gadm_CHN_0"

#Enter the cache configuration file (conf.xml) for your cached map service.
#This will give you and estimate on how many tiles will be generated for each extent
#cacheConfig = parse('C:/arcgisserver/arcgiscache/mapservice/Layers/conf.xml')
cacheConfig = parse('C:/Program Files/ArcGIS/Server/TilingSchemes/ArcGIS_Online_Bing_Maps_Google_Maps.xml')

#Enter the name of your ArcGIS Server
server_name = "seanpc"

#Enter the name of your predefined Cached Service
#If your service is in a folder then the syntax is: foldername/servicename
#If a service USAMap was in the basemap folder the syntax would be:
#service_name = "basemap/USAMap"
service_name = "SampleWorldCities"

#Enter the name of your predefined cached map dataframe
data_frame = "Layers"

#Enter the layers you wish to cache, leave blank to cache all layers
layers=""
#layers = "ushigh;counties;states"

#Enter scales you wish to cache.  These should be similar to the scales
#that you have already cached your service at.
#scales = "10000;7000;4000;2000;1000"
scales = "16000000;8000000;4000000;2000000;1000000;500000;250000;125000;64000;32000;16000;5000"

#Enter update mode.  Recreate All Tiles, replaces all tiles.
#Recreate Empty Tiles, replaces only empty tiles.
update_mode = "Recreate All Tiles"
#update_mode = "Recreate Empty Tiles"

#Enter the number of SOCs that you wish to cache with
#This can be no more than the max set for the service.
thread_count = "2"

#Whether you want to use Antialiasing or not.
antialiasing = "ANTIALIASING"
#antialiasing = "NONE"
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
    MinX = float(extent.split(' ')[0])
    MinY = float(extent.split(' ')[1])
    MaxX = float(extent.split(' ')[2])
    MaxY = float(extent.split(' ')[3])
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

        for scale in scales.split(';'):
            if scale == Scale:        
                ## Compute number of tiles wide.
                tileWidth = TileCols * Resolution
                tileColumn = math.floor((MinX - TileOriginX) / tileWidth)
                tileXMin = TileOriginX + (tileColumn * tileWidth)
                numTilesWideFromTile = math.ceil((MaxX - tileXMin) / tileWidth)
                tileXMax = tileXMin + (tileWidth * numTilesWideFromTile)
                print "LevelID= " + str(LevelID)
                print "Scale= " + str(Scale)
                print "Resolution= " + str(Resolution)
                print "numTilesWideFromTile = " + str(numTilesWideFromTile)
                
                ## Compute number of tiles high.
                tileHeight = TileRows * Resolution
                tileRow = math.floor((TileOriginY - MinY) / tileHeight)
                tileYMin = (TileOriginY - (tileRow * tileHeight)) - tileHeight
                numTilesHighFromTile = math.ceil((MaxY - tileYMin) / tileHeight)
                print "numTilesHighFromTile = " + str(numTilesHighFromTile)
                print "totalTiles= " + str(numTilesWideFromTile * numTilesHighFromTile)
                totalTiles += numTilesWideFromTile * numTilesHighFromTile
                print ""
    return totalTiles

# check input featureclass to see if the "Cached" field exists.  If it exists then
# proceed.  If it does not then add "Cached" field to the feature class
#if arcpy.ListFields(cacheFeatures,"CACHED").Next():
    #print "field Cached exists"
#else:
    #print "field does not exist"
    #arcpy.addfield (cacheFeatures, "CACHED", "TEXT")

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

rows = arcpy.da.SearchCursor(cacheFeatures,"OID@,Shape@")
row = rows.Next()

# While row is not empty (until all features have been processed) get the feature for
# the current row and use the getFeatureExtent function to get the feature extent.  Use
# the feature extent to call updateMapServerCache for the predefined scales and
# cache parameters.  If the cache finishes successfully then update the featureclass
# so that the Cached field reads 'true'.  If it does not finish successfully then the
# script will stop.  You can rerun the script with the current featureclass and it
# pick up at the row it left off at.
while row:
    feat = row.GetValue(shapefieldname)
    constraining_extent = feat.extent
    print "Updating envelope: " + str(row.GetValue(desc.OIDFieldName))
    print constraining_extent
    try:
        startTime = datetime.now()
        #arcpy.UpdateMapServerCache(server_name, service_name, data_frame, layers, constraining_extent, scales, update_mode, thread_count, antialiasing)
        #arcpy.UpdateMapServerCache_server(server_name, object_name, data_frame, layers, constraining_extent, scales, update_mode, thread_count, antialiasing)
        #print arcpy.GetMessages(1)
        #row.CACHED = "yes"
        #rows.UpdateRow(row)
        #endTime = datetime.now()
        #time_difference = endTime-startTime
        tileCount = handleTileCacheInfo(cacheConfig, constraining_extent)
        print "Total tiles generated for this extent: " + str(tileCount)
        #print 'elapsed', time_difference
        #print "Tiles generated per minute: " + str(tileCount/(time_difference.seconds / 60.0))
        print "Finished env update."
        print ""
        row = rows.Next()
    except:
        arcpy.AddMessage(arcpy.GetMessages(2))
        print arcpy.GetMessages(2)
        print "update failed, stop processing"
        del rows
        del arcpy
        sys.exit(1)


#release row ojbect
del rows

print "Update Complete"


