# -*- coding: utf-8 -*-
# ===========================================================================
# UpdateAddlParcel.py
# Created on: 5/23/18 by Ben Chou, Burbank GIS
# Revised 8/28/18
# Description: Updates GDB.AddlParcel on gis2.sde
# Comments: Path of database connection may have to be modified
# ===========================================================================

#---------------------------*EDIT IF NEEDED*---------------------------------------------------
# path of editable GDB.AddlParcel
addlParcel = "Database Connections\\gis2_GDB.sde\\GDB.AddlParcel"

# path of read-only GDB.Parcels
parcels = "Database Connections\\gdbuser.sde\\GDB.Administration\\GDB.Parcels"

# path of read-only GDB.Zoning
zoning = "Database Connections\\gdbuser.sde\\GDB.Administration\\GDB.Zoning"

# path of read-only GDB.Voter_Precincts
voterPrecincts = "Database Connections\\gdbuser.sde\\GDB.Administration\\GDB.Voter_Precincts"

# path of read-only GDB.Census_Block_Groups
censusBGs = "Database Connections\\gdbuser.sde\\GDB.Demographic\\GDB.Census_Block_Groups"

# path of read-only GDB.Trash_Truck_Days
trashDays = "Database Connections\\gdbuser.sde\\GDB.Operations\\GDB.Trash_Truck_Days"

# path of read-only GDB.Trash_Truck_Routes
trashRoutes = "Database Connections\\gdbuser.sde\\GDB.Operations\\GDB.Trash_Truck_Routes"

# path of read-only GDB.Street_Sweeping
streetSweep = "Database Connections\\gdbuser.sde\\GDB.Services\\GDB.Street_Sweeping"
#----------------------------------------------------------------------------------------------

raw_input('Are you sure you want to run this script to update GDB.AddlParcel? \nHave you checked the file paths in the script? \nPress Enter to continue.')

try:
    # Import arcpy, sys, os, and time modules
    import arcpy, sys, os, time

    def spatialJoin(fc1, fc2, outFields, count):
        # Create and load field maps from feature classes
        fieldMap = arcpy.FieldMappings()
        fieldMap.addTable(fc1)
        fieldMap.addTable(fc2)

        # Remove unwanted fields before performing spatial join
        [fieldMap.removeFieldMap(fieldMap.findFieldMapIndex(field)) for field in [f.name for f in fieldMap.fields if f.name not in outFields]]

        # Perform spatial join and return result
        outFC = "in_memory\\Output" + str(count)
        arcpy.SpatialJoin_analysis(fc1, fc2, outFC, field_mapping=fieldMap)
        return outFC

    def changeFields(layer, fields):
        # loop through pairs and change field names
        [arcpy.AlterField_management(layer, pair[0], pair[1]) for pair in fields]

    # Assign path for backup copy, get today's date, and overwrite output files
    path = r'\\chnfil01a\GIS\Temp\parcels'
    date = time.strftime('%m_%d_%Y')
    arcpy.env.overwriteOutput = True

    arcpy.AddMessage('')
    arcpy.AddMessage("Conducting spatial joins...")

    # Call spatial join function for GDB.Parcels and GDB.Zoning
    layer1 = spatialJoin(parcels, zoning, ['AIN','APN_STRING','SITUSZIP','NAMEA_ALF'], 1)

    # Call spatial join function for GDB.Voter_Precincts
    layer2 = spatialJoin(layer1, voterPrecincts, ['AIN','APN_STRING','SITUSZIP','NAMEA_ALF','PRECINCT'], 2)

    # Add string field for voter precincts
    arcpy.AddField_management(layer2, "VOTER_PRCN", "TEXT", "", "", "3")

    # Populate new field with voter precincts
    arcpy.CalculateField_management(layer2, "VOTER_PRCN", "str(!PRECINCT!)", "PYTHON_9.3")

    # Delete old short integer voter precinct field
    arcpy.DeleteField_management(layer2, "Join_Count;TARGET_FID;PRECINCT")

    # Call spatial join function for GDB.Census_Block_Groups
    layer3 = spatialJoin(layer2, censusBGs, ['AIN','APN_STRING','SITUSZIP','NAMEA_ALF','VOTER_PRCN','TRACTCE10','BLKGRPCE10'], 3)

    # Call spatial join function for GDB.Trash_Truck_Days
    layer4 = spatialJoin(layer3, trashDays, ['AIN','APN_STRING','SITUSZIP','NAMEA_ALF','VOTER_PRCN','TRACTCE10','BLKGRPCE10','ROUTE_DAY'], 4)

    # Call spatial join function for GDB.Trash_Truck_Routes
    layer5 = spatialJoin(layer4, trashRoutes, ['AIN','APN_STRING','SITUSZIP','NAMEA_ALF','VOTER_PRCN','TRACTCE10','BLKGRPCE10','ROUTE_DAY','ROUTE_NUM'], 5)

    # Call spatial join function for GDB.Street_Sweeping
    arcpy.AddMessage("Completing spatial joins...")
    layer6 = spatialJoin(layer5, streetSweep, ['AIN','APN_STRING','SITUSZIP','NAMEA_ALF','VOTER_PRCN','TRACTCE10','BLKGRPCE10','ROUTE_DAY','ROUTE_NUM','SWEEP_DAY'], 6)

    # List of field names to change to match GDB.AddlParcel
    fields = [['AIN','APN'], ['SITUSZIP','ZIP_CODE'], ['NAMEA_ALF', 'ZONE'],
    ['TRACTCE10','CENSUS_TRA'], ['BLKGRPCE10','BLOCK_GROU'], ['ROUTE_DAY','TRASH_DAY'],
    ['ROUTE_NUM','TRASH_ROUT']]

    # Call change fields function with list of fields
    changeFields(layer6, fields)

    # Clean up fields
    arcpy.DeleteField_management(layer6, "Join_Count;TARGET_FID")

    # Save new Addl Parcel table
    arcpy.AddMessage("Saving new Addl Parcel table to chnfil01a\gis\Temp\parcels\parcels_bak.gdb...")
    gdb = os.path.join(path, "parcels_bak.gdb\\")
    arcpy.CopyRows_management(layer6, gdb + "NewAddlParcel_" + date)

    # Make backup copy of GDB.AddlParcel
    arcpy.AddMessage("Saving backup copy of GDB.AddlParcel to chnfil01a\gis\Temp\parcels\parcels_bak.gdb...")
    arcpy.CopyRows_management(addlParcel, gdb + "AddlParcel_bak_" + date, "")

    # Delete all records in GDB.AddlParcel
    arcpy.AddMessage("Deleting all records in GDB.AddlParcel...")
    arcpy.DeleteRows_management(addlParcel)

    # Append updated records to GDB.AddlParcel
    arcpy.AddMessage("Appending updated records to GDB.AddlParcel...")
    arcpy.Append_management(gdb + "NewAddlParcel_" + date, addlParcel, "TEST")

    arcpy.AddMessage('')
    arcpy.AddMessage("Update of GDB.AddlParcel is complete.")
    arcpy.AddMessage('')
    raw_input("Press Enter to exit.")

except:
    arcpy.AddMessage('')
    arcpy.AddMessage("Error encountered.")
    arcpy.AddMessage(arcpy.GetMessages())
    raw_input("Press Enter to exit.")
