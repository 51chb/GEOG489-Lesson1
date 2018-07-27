# -----------------------------------------------------------------------------------------
# Name: MapTool.py
# Author: created by Ben Chou for GEOG 489, Final Project, June 2018
# Description: Connects core_functions.py with map_tool_gui.py to create map tool program
#------------------------------------------------------------------------------------------

import sys, webbrowser
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import QVariant, QUrl
from PyQt5.Qt import Qt

import pandas as pd
import geopandas as gpd
import core_functions, map_tool_gui

# ----------------------------------------
# GUI event handler and related functions
# ----------------------------------------

def browseFile1():              # open file dialog to select text file
    fileName, _ = QFileDialog.getOpenFileName(mainWindow,"Select file", "","All files (*.*)")
    if fileName:                # if file is selected, change line edit to file name, enable other objects
        ui.file1LE.setText(fileName)
        ui.checkBox.setEnabled(True)
        ui.delimiterLabel.setEnabled(True)
        ui.delimiterCB.setEnabled(True)
        populateCB()

def populateCB():               # populate the delimiter type combo box
    ui.delimiterCB.clear()      # clear all items from combo box
    delimiters = ['colon', 'comma', 'pipe', 'semi-colon', 'space', 'tab']     # list of delimiter types
    ui.delimiterCB.addItems(delimiters)     # add list to delimiter combo box
    ui.processPB.setEnabled(True)       # enable process data push button

def checkBox():                 # when check box for second file is checked, enable browsing for second file
    ui.file2LE.setEnabled(True)
    ui.browseFileTB2.setEnabled(True)

def browseFile2():              # open file dialog to select text file
    fileName2, _ = QFileDialog.getOpenFileName(mainWindow,"Select file", "","All files (*.*)")
    if fileName2:               # if file is selected, change line edit to file name
        ui.file2LE.setText(fileName2)

def setAttributesLV(attributes): # add fields from files to list view
    m = QStandardItemModel()
    for item in attributes:
        item = QStandardItem(item)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setData(QVariant(Qt.Unchecked), Qt.CheckStateRole)
        m.appendRow(item)
    ui.attributesLV.setModel(m)

def processData():              # read data into dataframes
    ui.statusbar.showMessage("Processing data...please wait.")
    global files                # create global variable to store file names

    if ui.delimiterCB.currentText() and ui.file1LE.text():
        delimiter = ui.delimiterCB.currentText()    # delimiter from combo box

        if ui.file2LE.text():                       # if second file selected, add filename to file list
            files = [ui.file1LE.text(), ui.file2LE.text()]

        else:                                       # if only one file, add filename to file list
            files = [ui.file1LE.text()]

        try:
            global dataframes, fields       # create global variables to store dataframes and fields
            dataframes = core_functions.createDF(files, delimiter)  # call create dataframes from raw text files function
            fields = core_functions.getFields(dataframes)   # call get fields from dataframes function

            ui.dataGB.setEnabled(True)                      # enable data group box and combo boxes
            ui.placeTypeCB.setEnabled(True)
            ui.placeFieldCB.setEnabled(True)
            ui.valueCB.setEnabled(True)
            ui.stateLE.setEnabled(True)

            place_types = ['City', 'County', 'State']       # list of place type options
            ui.placeTypeCB.clear()                          # clear combo box
            ui.placeTypeCB.addItems(place_types)            # populate combo box with place types

            ui.placeFieldCB.clear()                         # clear combo boxes
            ui.valueCB.clear()

            if len(dataframes) == 1:                # if there is only one dataframe, use the list of fields for combo boxes and list view
                ui.placeFieldCB.addItems(fields)
                ui.valueCB.addItems(fields)
                setAttributesLV(fields)

            else:                                   # if there are two dataframes, use respective field lists for each file
                ui.key1CB.setEnabled(True)          # enable key field combo boxes
                ui.key2CB.setEnabled(True)
                ui.key1CB.clear()                   # clear combo boxes
                ui.key2CB.clear()
                ui.key1CB.addItems(fields[0])       # populate combo box with field list from first dataframe
                ui.key2CB.addItems(fields[1])       # populate combo box with field list from second dataframe
                ui.placeFieldCB.addItems(fields[2]) # populate combo box with set of unique field names
                ui.valueCB.addItems(fields[2])      # populate combo box with set of unique field names
                setAttributesLV(fields[2])          # populate list view with set of unique field names

            ui.statusbar.showMessage("Please provide the required data inputs.")
        except Exception as e:
            QMessageBox.information(mainWindow, "Error", "Data processing could not be completed with " + str(e.__class__) + ": " + str(e), QMessageBox.Ok)
            ui.statusbar.clearMessage()

    else:                       # show error message if delimiter is not identified
        QMessageBox.information(mainWindow, 'Missing required input', 'Select the text delimiter type.', QMessageBox.Ok)

def enableTool():
    ui.outputGB.setEnabled(True)            # enable output groupbox
    ui.runPB.setEnabled(True)               # enable run push button

def saveShapefile():         # open new file dialog to save shapefile
    fileName, _ = QFileDialog.getSaveFileName(mainWindow,"Save new shapefile as", "","Shapefile (*.shp)")
    if fileName:
        ui.shapefileLE.setText(fileName)

def saveHtmlFile():         # open new file dialog to save html file
    fileName, _ = QFileDialog.getSaveFileName(mainWindow,"Save new html file as", "","Html (*.html)")
    if fileName:
        ui.htmlFileLE.setText(fileName)

def checkInputs():      # check for required inputs before running tool
    keys = []           # initialize local variables
    state = ''

    if ui.placeTypeCB.currentText() != 'County':    # if place type is not county, check to make sure inputs have been provided
        if len(files) == 1:
            if ui.placeTypeCB.currentText() and ui.placeFieldCB.currentText() and ui.valueCB.currentText() and ui.shapefileLE.text() and ui.htmlFileLE.text():
                run(keys, state)
            else:
                QMessageBox.information(mainWindow, 'Missing required input(s)', 'Please make sure that all required inputs have been specified.', QMessageBox.Ok)
        else:
            if ui.placeTypeCB.currentText() and ui.placeFieldCB.currentText() and ui.valueCB.currentText() and ui.key1CB.currentText() and ui.key2CB.currentText() and ui.shapefileLE.text() and ui.htmlFileLE.text():
                keys = [ui.key1CB.currentText(), ui.key2CB.currentText()]
                run(keys, state)
            else:
                QMessageBox.information(mainWindow, 'Missing required input(s)', 'Please make sure that all required inputs have been specified.', QMessageBox.Ok)

    else:                                           # if place type is county, check to make sure inputs have been provided
        if len(files) == 1:
            if ui.placeTypeCB.currentText() and ui.placeFieldCB.currentText() and ui.valueCB.currentText() and ui.stateLE.text() and ui.shapefileLE.text() and ui.htmlFileLE.text():
                state = ui.stateLE.text()
                run(keys, state)
            else:
                QMessageBox.information(mainWindow, 'Missing required input(s)', 'Please make sure that all required inputs have been specified.', QMessageBox.Ok)
        else:
            if ui.placeTypeCB.currentText() and ui.placeFieldCB.currentText() and ui.valueCB.currentText() and ui.stateLE.text() and ui.key1CB.currentText() and ui.key2CB.currentText() and ui.shapefileLE.text() and ui.htmlFileLE.text():
                state = ui.stateLE.text()
                keys = [ui.key1CB.currentText(), ui.key2CB.currentText()]
                run(keys, state)
            else:
                QMessageBox.information(mainWindow, 'Missing required input(s)', 'Please make sure that all required inputs have been specified.', QMessageBox.Ok)

def displayMap(html):                   # display map
    ui.tabwidget.setCurrentIndex(1)     # change tab index to map tab
    url = QUrl.fromLocalFile(html)
    ui.webView.load(url)                # display static map in tab
    webbrowser.open(html)               # open interactive map in web browser

def run(keys, state):      # call core functions to create geodataframe, shapefile, and map from data

    try:
        ui.statusbar.showMessage("Running tool...please wait.")

        # assign user inputs to variables
        place = ui.placeTypeCB.currentText()
        placeField = ui.placeFieldCB.currentText()
        valueField = ui.valueCB.currentText()
        outShapefile = ui.shapefileLE.text()
        outHtml = ui.htmlFileLE.text()

        # get attribute fields from list view
        attributes = []
        if len(files) == 1:
            for i in range(ui.attributesLV.model().rowCount()):
                if ui.attributesLV.model().item(i).checkState() == Qt.Checked:
                    attributes.append(fields[i])
        else:
            for i in range(ui.attributesLV.model().rowCount()):
                if ui.attributesLV.model().item(i).checkState() == Qt.Checked:
                    attributes.append(fields[2][i])

        # set projections: WGS84 projection for geopanda and WKT for shapefile
        crs4326 = {'init': 'epsg:4326'}
        crs = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'

        # merge dataframes and only keep desired attribute fields
        merged_df = core_functions.mergeDataframes(dataframes, keys)
        merged_df = merged_df[attributes]

        # create geometry based on place type specified
        createGeometry = {'City': core_functions.createPoints, 'County': core_functions.createPolygons, 'State': core_functions.createPolygons}
        geometryList = merged_df.apply(createGeometry[place], place=place, column=placeField, state=state, axis=1)

        # create geopanda with geometry and write data to shapefile
        dataframeGeo = gpd.GeoDataFrame(merged_df, crs=crs4326, geometry=geometryList)
        dataframeGeo.to_file(outShapefile, crs_wkt=crs)

        # create folium map object from geodataframe, add features to map, and save as html file
        core_functions.createMap(place, dataframeGeo, placeField, valueField, outHtml)

        # display map in GUI by calling function
        displayMap(outHtml)

        ui.statusbar.showMessage("Success! Tool has created shapefile and map.")
        ui.runPB.setEnabled(False)

    except Exception as e:
            QMessageBox.information(mainWindow, "Error", "Tool could not successfully run with " + str(e.__class__) + ": " + str(e), QMessageBox.Ok)
            ui.statusbar.clearMessage()

#------------------------------------------
# Create app and main window
#------------------------------------------
app = QApplication(sys.argv)

# set up main window
mainWindow = QMainWindow()
ui = map_tool_gui.Ui_MainWindow()
ui.setupUi(mainWindow)
ui.statusbar.showMessage("Provide required input file(s).")
ui.webView.setHtml('<h1> A map has not been created yet. </h1>')

#------------------------------------------
# Connect signals to slots
#------------------------------------------
ui.browseFileTB.clicked.connect(browseFile1)
ui.checkBox.stateChanged.connect(checkBox)
ui.browseFileTB2.clicked.connect(browseFile2)
ui.processPB.clicked.connect(processData)
ui.attributesLV.clicked.connect(enableTool)
ui.shapefileTB.clicked.connect(saveShapefile)
ui.htmlFileTB.clicked.connect(saveHtmlFile)
ui.runPB.clicked.connect(checkInputs)
ui.cancelPB.clicked.connect(app.quit)

#------------------------------------------
# Run app
#------------------------------------------
mainWindow.show()
sys.exit(app.exec_())






