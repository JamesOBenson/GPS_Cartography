#!/usr/bin/env python
"""
This program requires python3 and a user to input a center latitude and a center longitude.
It will then plot that point in blue on a google maps, along with a circular radius.
If you provide a google API_Key, you can then plot those point and create a driving route based off
those points.

This can be executed by issuing: 
python gps.py
or pythonw gps.py if you are on a mac with conda installed.

"""

import math
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.io.img_tiles as cimgt
import urllib.request
import json

# Inputs
#Place your API key here
API_KEY = ""
RADIUS = 3218.69 #2 Miles in meters; the following code is an approximation
#                  that stays reasonably accurate for distances < 100km
CENTER_LAT = 29.4232653 # Latitude of circle center, decimal degrees
CENTER_LONG = -98.5041371 # Longitude of circle center, decimal degrees
N = 100
#For distances of:
# State size distances, a zoom of 10 or less.
# A few miles, I recommend a zoom of 10-14
# Under 1 mile, zoom of 15-17
ZOOM = 14 # 10 City, 15 Streets, 20 Buildings
BOX = RADIUS*0.20  # This will be 20% larger box than plot needed
M_2_DEG = 0.0000089831117499


###################################
#  Generate circle radius points  #
###################################
LatPoints = []
LongPoints = []
circlePoints = []
for k in range(N):
    # compute
    angle = math.pi*2*k/N
    dx = RADIUS*math.cos(angle)
    dy = RADIUS*math.sin(angle)
    point = {}
    point['lat'] = CENTER_LAT + (180/math.pi)*(dy/6378137)
    point['lon'] = CENTER_LONG + (180/math.pi)*(dx/6378137)/math.cos(CENTER_LAT*math.pi/180)
    # add to list
    LatPoints.append(point['lat'])
    LongPoints.append(point['lon'])
    circlePoints.append(point)
#print(LongPoints)

#################################
#  Determine boundaries of map  #
#################################
new_latitude_upper = CENTER_LAT  + RADIUS*M_2_DEG + BOX*M_2_DEG
new_latitude_lower = CENTER_LAT  - RADIUS*M_2_DEG - BOX*M_2_DEG
new_longitude_upper = CENTER_LONG + RADIUS*M_2_DEG + 4*BOX*M_2_DEG  # 4 here is a fudge factor
new_longitude_lower = CENTER_LONG - RADIUS*M_2_DEG - 4*BOX*M_2_DEG  # 4 here is a fudge factor
#print(new_latitude_upper)
#print(new_latitude_lower)
#print(new_longitude_upper)
#print(new_longitude_lower)

###############
#  Create map #
###############
""" This function will go and create a plot, note, sometimes GoogleTiles is finicky and
it will fail based off of Google's server load I suspect"""
def make_map(projection=ccrs.PlateCarree()):
    fig, ax = plt.subplots(figsize=(15, 20),
                           subplot_kw=dict(projection=projection))
    gl = ax.gridlines(draw_labels=True)
    gl.xlabels_top = gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    return fig, ax

extent = [new_longitude_lower, new_longitude_upper, new_latitude_lower, new_latitude_upper]
# options are satellite, street (default), terrain, only_streets
request = cimgt.GoogleTiles(style='street')
fig, ax = make_map(projection=request.crs)


# This tests if the API key is here or not...
# If not, then don't run, if provided, run.
if API_KEY:
    ##############################
    #  Snap GPS points to roads  #
    ##############################
    RoadLatPoints = []
    RoadLongPoints = []

    ####################################
    #  Create the URL for the points.  #
    ####################################
    url="https://roads.googleapis.com/v1/snapToRoads?path="
    googlemapsGPSString=''.join([str(a)+','+str(b)+'|' for a,b in zip(LatPoints,LongPoints)])
    googlemapsGPSString=googlemapsGPSString[:-1]
    googlemapsGPSENDString="&interpolate=true&key="+API_KEY
    myURL=url+googlemapsGPSString+googlemapsGPSENDString
    #print(myURL)

    req = urllib.request.Request(url=myURL)
    f = urllib.request.urlopen(req)
    json = json.loads(f.read())

    for mylocation in json['snappedPoints']:
    #    print(mylocation['originalIndex'])
        for k, v in mylocation.items():
            #########################
            #print off lat & long.  #
            #########################
            try:
                #This is getting a dictionary of Latitude and Longitude
                for LatLongLable,val in v.items():
                    if LatLongLable=='latitude':
                        RoadLatPoints.append(val)
                    if LatLongLable=='longitude':
                        RoadLongPoints.append(val)
                    #print(LatLongLable)
                    #print(val)
            except AttributeError:
                continue
    #print(RoadLatPoints)
    #print(RoadLongPoints)

    for point in RoadLatPoints:
        ax.plot(RoadLongPoints, RoadLatPoints, marker='o', color='green', markersize=5,
                 alpha=0.7, transform=ccrs.Geodetic())
    
#####################
#  Plot GPS Points  #
#####################
# Plot the center point
ax.plot(CENTER_LONG, CENTER_LAT, marker='o', color='blue', markersize=5,
        alpha=0.7, transform=ccrs.Geodetic())

#Plot the circle radius
for point in LatPoints:
    ax.plot(LongPoints, LatPoints, marker='o', color='red', markersize=5,
            alpha=0.7, transform=ccrs.Geodetic())

ax.set_extent(extent)
ax.add_image(request, ZOOM)
fig.savefig('GPS_figure.png')
