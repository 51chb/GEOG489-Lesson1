# import required packages and modules
import os, urllib.parse, requests, geojson
import numpy as np
import pandas as pd
from shapely.geometry import Point, shape, mapping
import geopandas as gpd
import folium

def createDF(files, delimiter):             # create list of dataframes from raw text files
    delimiters = {'colon': ':', 'comma': ',', 'pipe': '|', 'semi-colon': ';', 'space': ' ', 'tab':'\t'}     # dictionary of delimiter types
    dataframes = []
    for file in files:                      # loop through files, create dataframe by reading file
        name = 'df' + str(files.index(file))
        name = pd.read_csv(file, sep=delimiters[delimiter], header=0)
        dataframes.append(name)
    return dataframes

def getFields(dataframes):                  # get list of fields in each dataframe and set of unique fields for all dataframes
    if len(dataframes) == 1:
        fields1 = list(dataframes[0])
        return fields1
    else:
        fields1 = list(dataframes[0])
        fields2 = list(dataframes[1])
        fields3 = list(set(fields1 + fields2))
        return [fields1, fields2, fields3]

def mergeDataframes(dataframes, keys):      # merge dataframes using key values
    if len(dataframes) == 1:                # if one dataframe, return dataframe
        return dataframes[0]
    else:                                   # if two dataframes, merge dataframes on key values
        merged_df = dataframes[0].merge(dataframes[1], left_on=keys[0], right_on=keys[1])
        return merged_df

def queryNominatim(query, limit = 1, countryCode = 'US'):       # query nominatim web service with parameters provided and return feature as JSON
    nominatimBaseURL = 'https://nominatim.openstreetmap.org/search?'
    # setup strings for query parameters and build query url
    countryCodeParameter = '&countrycodes=' + urllib.parse.quote(countryCode)
    limitParameter = '&limit=' + str(limit)
    queryURL = nominatimBaseURL + query + '&format=json' + countryCodeParameter + limitParameter

    # run query and return JSON response
    r = requests.get(queryURL)
    return r.json()

def queryOSM(relationID):                   # for polygons, query OSM using relation ID to get ways and nodes
    OSMbaseURL = 'http://polygons.openstreetmap.fr/get_geojson.py'
    osmURL = OSMbaseURL + '?id=' + str(relationID) + '&params=0'

    # run query and return GeoJSON response
    g = requests.get(osmURL)
    return geojson.loads(g.content)

def createPoints(row, place, column, state):# create point geometry for rows by calling nominatim query with place information
    queryString = 'q='+ row[column]
    item = queryNominatim(queryString)
    if item:                                # if item returned from query, create point object from lat,lon coordinates
        p = Point(float(item[0]['lon']), float(item[0]['lat']))
        return p

def createPolygons(row, place, column, state):     # create polygon geometry for rows by calling nominatim and OSM queries with place info
    queryString = {'County': place.lower() + '=' + row[column] + '&' + 'state=' + state, 'State': place.lower() + '=' + row[column]}    # dictionary of query strings based on place type
    item = queryNominatim(queryString[place])
    if item:                                # if item returned from query, create shape object from lat,lon coordinates
        relationID = item[0]['osm_id']
        polygon = shape(queryOSM(relationID))
        return polygon[0]

def addPoints(row, mapobj, id_field, value_field):  # add points and popups to map object
    # place circle marker at each point using coordinates, create popup with attribute info, and add to map object
    folium.CircleMarker(location = [row.geometry.y, row.geometry.x], radius=5, fill=True, popup=folium.Popup('<strong>' + row[id_field] + '</strong>' + '<br>' + value_field + ': ' + '<strong>' + str(row[value_field]) + '</strong>')).add_to(mapobj)

def addPopup(row, mapobj, id_field, value_field):   # add popups for polygons to map object
    # place polygon marker, create popup with attribute info, and add to map object
    folium.features.PolygonMarker(locations = [(item[1],item[0]) for item in mapping(row.geometry)['coordinates'][0][0]], color='None', fill_opacity=0, popup=folium.Popup('<strong>' + row[id_field] + '</strong>' + '<br>' + value_field + ': ' + '<strong>' + str(row[value_field]) + '</strong>')).add_to(mapobj)

def addChoropleth(gdf, mapobj, id_field, value_field, fill_color = 'BuGn', fill_opacity = 0.7, line_opacity = 0.2):     # add choropleth symbology for polygons
    # call choropleth function, specify geometry as geodataframe converted to GeoJSON, data as geodataframe, layer name as value field, columns as the user-specified id field and and value field
    mapobj.choropleth(geo_data=gdf.to_json(), data=gdf, name=value_field, columns=[id_field, value_field], key_on='feature.properties.{}'.format(id_field), fill_color=fill_color, fill_opacity=fill_opacity, line_opacity=line_opacity, legend_name=value_field, reset=True)
    # add popups to map for all rows
    gdf.apply(addPopup, mapobj=mapobj, id_field=id_field, value_field=value_field, axis=1)

def createMap(place, gdf, id_field, value_field, outHtml): # create map object centered based on features
    zoom = {'City': 4, 'County': 6, 'State': 4}            # set zoom level based on place type
    mapobj = folium.Map(location=[gdf.unary_union.centroid.y, gdf.unary_union.centroid.x], tiles='Cartodb Positron', zoom_start=zoom[place])    # set map center based on features, basemap, zoom level
    if place == 'City':                                    # if cities, add points to map object
        gdf.apply(addPoints, mapobj=mapobj, id_field=id_field, value_field=value_field, axis=1)
    else:                                                  # if counties or states, add polygons to map object
        addChoropleth(gdf, mapobj, id_field, value_field)
    mapobj.save(outHtml)                                   # save map object to html file