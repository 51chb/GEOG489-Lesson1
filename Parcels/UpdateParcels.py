# -*- coding: utf-8 -*-
# ===========================================================================
# UpdateParcels.py
# Created on: 7/25/18 by Ben Chou, Burbank GIS
# Revised 8/28/18
# Description: Updates GDB.Parcels on gis2.sde with quarterly assessor data
# Comments: Path of database connections may have to be modified
# ===========================================================================

#------------------------------*EDIT IF NEEDED*-------------------------------------------------
# path of quarterly parcel data from County Assessor
newData = r'\\chnfil01a\gis\Temp\parcels\parcels_7_3_2018.gdb\burbank_parcels_assr'

# path of read-only GDB.Parcels
parcels = 'Database Connections\\gdbuser.sde\\GDB.Administration\\GDB.Parcels'

# path of editable GDB.Parcels
gdb_parcels = 'Database Connections\\gis2_GDB.sde\\GDB.Administration\\GDB.Parcels'
#-----------------------------------------------------------------------------------------------

raw_input('Are you sure you want to run this script to update GDB.Parcels? \nHave you modified the file paths in the script? \nPress Enter to continue.')

try:
    import os, sys, re, arcpy, time

    def changeFields(layer, fields):
        # loop through pairs and change field names
        [arcpy.AlterField_management(layer, pair[0], pair[1]) for pair in fields]

    def addFields(layer, fields):
        # loop through and add fields
        [arcpy.AddField_management(layer, field[0], field[1], field[2], field[3], field[4]) for field in fields]

    def calculateFields(layer, fields, expr = 'PYTHON_9.3'):
        # loop through and calculate fields
        [arcpy.CalculateField_management(layer, field[0], field[1], expr, field[2]) for field in fields]

    poolCode = """def checkPool(useCode):
        pattern = '^(0[1-5].[1|34])|(652.)$'
        compiledRE = re.compile(pattern)

        if compiledRE.match(useCode):
            return 'Yes'"""

    heatCoolCode = """def checkHeatCool(dType1, dType2, dType3, dType4, dType5):
        pattern = '^0(1[1-4].|[2-5][23].)$'
        compiledRE = re.compile(pattern)

        if compiledRE.match(dType1) or compiledRE.match(dType2) or compiledRE.match(dType3) or compiledRE.match(dType4) or compiledRE.match(dType5):
            return 'Yes'"""

    # overwrite existing outputs and set workspace to in memory
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = "in_memory"

    # assign path for back-up copy, temp layer name & get today's date
    path = r'\\chnfil01a\GIS\Temp\parcels'
    layer = 'temp_layer'
    date = time.strftime('%m_%d_%Y')

    # fields to rename to match parcel fields
    fieldPairs = [['HOMEOWNEXMS','HOMEOWNEXM'], ['SITUSADDR','SADDRESS'],
    ['IMPRBASEVAL','IMPRBASEVA'], ['HOMEOWNEXMVAL','HOMEOWNE_1'],
    ['BOOK','ASSESSOR_B'], ['SITUSCITYST','SITUSCITYS'],
    ['TRANSFEREE2','TRANSFER_1'], ['BOOKPAGE','ASSESSOR_L'],
    ['PERSPROPVAL','PERSPROPVA'], ['OWNERSHIPCODE','OWNERSHIPC'],
    ['REALESTEXMVAL','REALESTEXM'], ['TRANSFEREE1','TRANSFEREE'],
    ['BOOKPAGELOT','APN_STRING'], ['SALE3AMOUNT','SALE3AMOUN'],
    ['DOCTRANSTAX','DOCTRANSTA'], ['SALE2AMOUNT','SALE2AMOUN'],
    ['PERSPROPEXMVAL','PERSPROPEX'], ['PERSPROPKEY','PERSPROPKE'],
    ['LANDBASEVAL','LANDBASEVA'], ['EXEMPTCLMTYPE','EXEMPTCLMT'],
    ['FIXTUREEXMVAL','FIXTUREEXM'], ['SALE1AMOUNT','SALE1AMOUN']]

    # new fields to add to layer
    newFields = [['TOTALBEDS', 'SHORT', '5', '', ''],
    ['RESQFT', 'DOUBLE', '38', '8', ''],
    ['ASSDVAL_1', 'TEXT', '', '', '25'],
    ['ASSDVAL', 'LONG', '10', '', ''],
    ['TOTALBATHS', 'SHORT', '5', '', ''],
    ['POOL', 'TEXT', '', '', '3'],
    ['COOL_HEAT', 'TEXT', '', '', '3'],
    ['NOTIFY', 'TEXT', '', '', '5']]

    # formulas to calculate new fields
    calculations = [['TOTALBEDS', '!BLDG1BEDS! + !BLDG2BEDS! + !BLDG3BEDS! + !BLDG4BEDS! + !BLDG5BEDS!', ''],
    ['ASSDVAL', '!LANDVAL! + !IMPRVAL!', ''],
    ['ASSDVAL_1', 'str(!ASSDVAL!)', ''],
    ['RESQFT', '!BLDGSTOTSQFT!', ''],
    ['TOTALBATHS', '!BLDG1BATHS! + !BLDG2BATHS! + !BLDG3BATHS! + !BLDG4BATHS! + !BLDG5BATHS!', ''],
    ['POOL', 'checkPool(!USECODE!)', poolCode],
    ['COOL_HEAT', 'checkHeatCool(!BLDG1DTYPE!, !BLDG2DTYPE!, !BLDG3DTYPE!, !BLDG4DTYPE!, !BLDG5DTYPE!)', heatCoolCode]]

    # make working copy of quarterly data
    arcpy.AddMessage('')
    arcpy.AddMessage('Making working copy of new quarterly parcel data...')
    arcpy.CopyFeatures_management(newData, 'dataCopy')
    arcpy.MakeFeatureLayer_management('dataCopy', layer)

    # call change fields function
    arcpy.AddMessage('Changing field names to match fields in GDB.Parcels...')
    changeFields(layer, fieldPairs)

    # call add fields function
    arcpy.AddMessage('Adding new fields...')
    addFields(layer, newFields)

    # call calculate fields function
    arcpy.AddMessage('Calculating new field values...')
    calculateFields(layer, calculations)

    # join GDB.Parcels to layer, calculate notify field, remove join
    arcpy.AddMessage('Calculating NOTIFY field...')
    arcpy.AddJoin_management(layer, 'AIN', parcels, 'AIN')
    arcpy.CalculateField_management(layer, 'NOTIFY', '!' + os.path.basename(parcels) + '.NOTIFY!', 'PYTHON_9.3')
    arcpy.RemoveJoin_management(layer)

    # save copy of new parcel feature class
    arcpy.AddMessage('Saving copy of new parcel feature class to chnfil01a\gis\Temp\parcels\parcels_bak.gdb...')
    gdb = os.path.join(path, 'parcels_bak.gdb\\')
    arcpy.CopyFeatures_management(layer, gdb + 'NewParcels_' + date)

    # save backup copy of GDB.Parcels
    arcpy.AddMessage('Saving backup copy of GDB.Parcels to chnfil01a\gis\Temp\parcels\parcels_bak.gdb...')
    arcpy.CopyFeatures_management(gdb_parcels, gdb + 'parcels_bak_' + date)

    # delete all records in GDB.Parcels
    arcpy.AddMessage('Deleting all records in GDB.Parcels...')
    arcpy.DeleteRows_management(gdb_parcels)

    # append updated records to GDB.Parcels
    arcpy.AddMessage('Appending updated records to GDB.Parcels...')
    arcpy.Append_management(gdb + 'NewParcels_' + date, gdb_parcels, 'NO_TEST', '', '')

    arcpy.AddMessage('')
    arcpy.AddMessage('Update of GDB.Parcels is complete.')
    arcpy.AddMessage('')
    raw_input('Press Enter to exit.')

except:
    arcpy.AddMessage('')
    arcpy.AddMessage('Error encountered.')
    arcpy.AddMessage(arcpy.GetMessages())
    raw_input('Press Enter to exit.')










