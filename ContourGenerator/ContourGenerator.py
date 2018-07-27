# Author: Ben Chou for Final Project, GEOG 485, Penn State
# Date: December 2017

# Purpose: Creates contour lines by parsing all text file(s) in a target folder, which contain GPS coordinates of continuous phemonena 

# ---FUNCTIONS---

# Creates a function that processes header of text file & returns list of index position of desired fields 
def processHeader(field1, field2):
    header = csvReader.next()
    header = [item.upper() for item in header]
    nameIndex = header.index(field1)
    valIndex = header.index(field2)
    latIndex = header.index("LATITUDE")
    lonIndex = header.index("LONGITUDE")
    list = [nameIndex, valIndex, latIndex, lonIndex]
    return list

# Creates a function that creates a new feature class & adds desired fields to attribute table
def createFC(coord, folder, fileName, field1, field2):
    spatialRef = arcpy.SpatialReference(coord)
    newFC = arcpy.CreateFeatureclass_management(folder, fileName, "POINT", "", "", "", spatialRef)
    arcpy.AddField_management(newFC, field1, "TEXT", "", "", 50)
    arcpy.AddField_management(newFC, field2, "FLOAT", "", "", 50)        

# Creates a function that creates a point object and writes desired values and geometry to feature class
def createPoints(ID, value, X, Y):
    point = arcpy.Point(X, Y)
    cursor.insertRow((ID, value, point))

# Creates a function that returns a raster based on a desired interpolation method
def createRaster (method, feature, value):
    if method == "IDW":
        rast = arcpy.sa.Idw(feature, value)
    elif method == "Kriging":
        kModel = arcpy.sa.KrigingModelOrdinary("SPHERICAL")
        rast = arcpy.sa.Kriging(feature, value, kModel)
    elif method == "Natural_Neighbor":
        rast = arcpy.sa.NaturalNeighbor(feature, value)
    elif method == "Spline":
        rast = arcpy.sa.Spline(feature, value)
    elif method == "Trend":
        rast = arcpy.sa.Trend(feature, value)
    return rast

# ---MAIN BODY OF SCRIPT---

try:
    # Imports CSV module and ArcPy site package    
    import csv
    import arcpy

    # Establishes workspace 
    arcpy.env.workspace = arcpy.GetParameterAsText(0)

    # Assigns variable to delimiter parameter, looks up delimiter in dictionary, and returns delimiter character
    delimiter = arcpy.GetParameterAsText(1)
    delimiterLookup = {"Colon": ":", "Comma": ",", "Pipe": "|", "Semi-colon": ";", "Space": " ", "Tab": "\t"}
    delimiterType = delimiterLookup[delimiter]

    # Assigns variables to input parameters
    nameField = arcpy.GetParameterAsText(2).upper()
    valField = arcpy.GetParameterAsText(3).upper() 
    gdb = arcpy.GetParameterAsText(4) + ".gdb"
    path = arcpy.env.workspace + "\\" + gdb + "\\"
    fc = arcpy.GetParameterAsText(5)
    WKID = int(arcpy.GetParameterAsText(6))
    interpolMethod = arcpy.GetParameterAsText(7)
    contFC = arcpy.GetParameterAsText(8)
    contInt = arcpy.GetParameterAsText(9)
    unique = arcpy.GetParameter(10)

    # Obtains list of text/CSV files in target folder
    files = arcpy.ListFiles("*.txt" or "*.csv")

    # Creates file geodatabase
    arcpy.CreateFileGDB_management(arcpy.env.workspace, gdb)

    # Runs code if data in each text file should be written to unique feature class and have unique contours generated
    if unique is True:

        # Loops through each file in the target folder 
        for file in files:

            # Opens text file, sets up CSV reader, and calls function to process header   
            gpsPoints = open(arcpy.env.workspace + "\\" + file)
            csvReader = csv.reader(gpsPoints, delimiter = delimiterType)
            index = processHeader(nameField, valField)

            # Obtains root file name, establishes feature class name, and calls function to create new feature class      
            rootName = file.rsplit('.', 1)[0]
            fcName = rootName + "_" + fc
            createFC(WKID, gdb, fcName, nameField, valField)

            # Writes desired values and point geometries to new feature class by using an insert cursor and calling function to create point objects 
            with arcpy.da.InsertCursor(path + fcName, (nameField, valField, "SHAPE@")) as cursor:
                for row in csvReader:
                    name = row[index[0]]
                    val = row[index[1]]
                    lat = row[index[2]]
                    lon = row[index[3]]
                    createPoints(name, val, lat, lon)
    
            # Checks out spatial analyst extension and calls function to create raster  
            arcpy.CheckOutExtension("Spatial")
            raster = createRaster(interpolMethod, path + fcName, valField)

            # Creates contour lines from raster
            arcpy.sa.Contour(raster, path + rootName + "_" + contFC, contInt)

            # Checks in spatial analyst extension and deletes raster
            arcpy.CheckInExtension("Spatial")
            del raster

            # Reports success message when contour lines have been created
            arcpy.AddMessage("Contour lines successfully created from data in %s." % (file))

    # Runs code if data in text files should be written to a single feature class and have one set of contours generated        
    else: 

        # Calls function to create new feature class
        createFC(WKID, gdb, fc, nameField, valField)

        # Loops through each file in the target folder
        for file in files:
    
            # Opens text file, sets up CSV reader, and calls function to process header 
            gpsPoints = open(arcpy.env.workspace + "\\" + file)
            csvReader = csv.reader(gpsPoints, delimiter = delimiterType)
            index = processHeader(nameField, valField)

            # Writes desired values and point geometries to the new feature class by using an insert cursor and calling function to create point objects
            with arcpy.da.InsertCursor(path + fc, (nameField, valField, "SHAPE@")) as cursor:
                for row in csvReader:
                    name = row[index[0]]
                    val = row[index[1]]
                    lat = row[index[2]]
                    lon = row[index[3]]
                    createPoints(name, val, lat, lon)

        # Checks out spatial analyst extension and calls function to create raster 
        arcpy.CheckOutExtension("Spatial")
        raster = createRaster(interpolMethod, path + fc, valField)

        # Creates contour lines from raster
        arcpy.sa.Contour(raster, path + contFC, contInt)

        # Checks in spatial analyst extension and deletes raster
        arcpy.CheckInExtension("Spatial")
        del raster

        # Reports success message when contour lines have been created
        arcpy.AddMessage("Contour lines successfully created from data in %s." % (arcpy.env.workspace))

except:
    arcpy.AddMessage("Error(s) encountered!")
    arcpy.GetMessages()
    


    
    
    