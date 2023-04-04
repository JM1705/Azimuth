# Main CompassBG script
from datetime import datetime, timedelta
codeInitTime = datetime.now()

# Print but with timestamp and stuff
def advPrint(string):
    timeUntilNow = (datetime.now()-codeInitTime)
    print('['+str(round(timeUntilNow.total_seconds(),3))+'s]: '+string)

advPrint("Loading liblaries")
import compass
from json import load
from random import randint
from os import listdir, getenv, path, getcwd
from types import SimpleNamespace
from fileCodeTranslate import translateDict
from dateutil import tz, parser
from requests import get
from sys import exit as sysexit
from time import sleep
from pathlib import Path


# Get paths
scriptLoc = path.dirname(path.realpath(__file__))
appdata = getenv('LOCALAPPDATA') + '\Azimuth'
bgpath = str(Path.home())+"\\Pictures\\Azimuth"

# Print versions
advPrint("Versions: ")
with open(scriptLoc+"\\azimuth.version","r") as version:
    advPrint("  Azimuth v"+version.read())
with open(appdata+"\\pref.json","r") as pref:
    advPrint("  Preferences file for v"+load(pref)['Version'])
with open(appdata+"\\cfg.json","r") as config:
    advPrint("  Config file for v"+load(config)['version'])
with open(appdata+"\\style.json","r") as style:
    style = load(style)
    advPrint("  \""+style['Name']+"\" style by "+style["Author"]+" for v"+style['Version'])

# Wait for internet connection
advPrint("Waiting for internet connection.")
connected = False
while not connected:
    try:
        request = get('https://archlinux.org', timeout=1)
        advPrint("Connected to the internet")
        connected = True
    except:
        pass

# Load config file as dictionary
tempCfg = load(open(appdata + "\\cfg.json", 'r'))
# Change the names of keys so the code doesn't break
tempCfg = translateDict(tempCfg, "code")
# Convert dictionary to namespace 
cfg = SimpleNamespace(**tempCfg)

# Select background from folder
if len(listdir(bgpath)) == 0:
    advPrint("There are no background images in the directory at "+bgpath+", please put one or more in there.")
    sleep(5)
    exit()
bgs = []
for file in listdir(bgpath):
    bgs.append(file)
sbgpath = bgpath+"\\"+bgs[randint(0, len(bgs)-1)]

# UTC to Local
def compassTimeTo24h(timeStr):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = parser.parse(timeStr.replace('Z', ''))
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    return central.strftime('%H:%M')

# Get time information
now = datetime.now()
todayDate = now.strftime("%Y-%m-%d")
# todayDate = "2023-03-30"
advPrint("Date: "+todayDate)

def getPeriods(unm, pwd, schoolcode):
    advPrint("Authenticating with Compass")
    c = compass.CompassAPI(unm, pwd, schoolcode)
    advPrint("Getting events list")
    events = c.get_calender_events_by_user(todayDate)

    periods = []
    for period in events:
        periodInfo = {}
        periodInfo["title"]=period["title"]
        periodInfo["starttime"]=period["start"]
        periodInfo["finishtime"]=period["finish"]

        instanceId=period["instanceId"]
        advPrint("Getting lesson info for "+periodInfo["title"])
        lessons = c.get_lessons_by_instance_id(instanceId)
        periodInfo["instanceId"]=instanceId
        
        lessonInstanceId=0
        for i in range(len(lessons['Instances'])):
            lessonInstance = lessons['Instances'][i]
            if lessonInstance['st'] == period["start"]:
                lessonInstanceId=i
            periodInfo['teachercode']=lessonInstance['m']

        periodInfo['location']=lessons['Instances'][lessonInstanceId]['LocationDetails']['shortName']

        periods.append(periodInfo)
    return periods

    
(unm, pwd, schoolcode)=(cfg.unm, cfg.pwd, cfg.schoolcode)

periods = getPeriods(unm, pwd, schoolcode)

for i in periods:
    i["starttime"]=compassTimeTo24h(i["starttime"])
    i["finishtime"]=compassTimeTo24h(i["finishtime"])

from datetime import datetime
# Convert string to datetime object, get length in seconds
# Converting str to datetime and str and datetime, can be made simpler :)
for i in periods:
    i['startdatetime']=datetime.strptime(i['starttime'],"%H:%M")
    i['finishdatetime']=datetime.strptime(i['finishtime'],"%H:%M")
    i['length']=(i['finishdatetime']-i['startdatetime'])

# Find length, start, end of day
dayLength=0
dayStart=0
dayFinish=0
for i in periods:
    if dayStart==0 or i['startdatetime']<dayStart:
        dayStart=i['startdatetime']
    if dayFinish==0 or i['finishdatetime']>dayFinish:
        dayFinish=i['finishdatetime']
dayLength=(dayFinish-dayStart)

# Check that there are events scheduled
if dayLength == 0:
    advPrint("There are no scheduled events today. Exiting")
    sleep(3)
    sysexit()

# Find position of periods
for i in periods:
    i['position']=i['startdatetime']-dayStart

# Sort periods by length
periods.sort(key=lambda item: item.get('length'))

# Import liblaries for drawing the UI
advPrint("Loading the rest of the liblaries")
from PIL import Image, ImageDraw, ImageFont
from screeninfo import get_monitors
from colorsys import hsv_to_rgb
import hashlib
from ctypes import windll

# Import files
pref=load(open(appdata+"\pref.json"))
subjectColours=pref['SubjectColours']
darkmode=pref['Darkmode']
includeTeacher=pref['IncludeTeacher']

style=load(open(appdata+"\style.json")) 
seperator=style['Seperator']                        # The character used to seperate properties in the period display
timelineoffset = style['TimelineOffset']            # How much the timeline is offset from the top of the display
timelinetextoffset = style['TimelineTextOffset']    # How much the timeline is offset from the timeline text
baseyoffset = style['BaseYOffset']                  # How much the period display is offset from the timeline
height = style['Height']                            # Height of each period
periodyspace = style['PeriodYSpace']                # Space between periods when they are stacked
periodxspace = style['PeriodXSpace']                # Amount to subtract from the width of a period
widthreduce = style['WidthReduce']                  # Double the space between the edge of the display to the UI
longticklength = style['LongTickLength']            # Length of the long ticks
longtickthickness = style['LongTickThickness']      # Thickness of the long ticks
shortticklength = style['ShortTickLength']          # Length of the short ticks
shorttickthickness = style['ShortTickThickness']    # Thickness of the short ticks
roundradius = style['RoundRadius']                  # Radius of squares for periods
fontsize = style['FontSize']                        # Size of text

font=ImageFont.truetype(scriptLoc+"\Inter-SemiBold.otf", size=fontsize)
heightIncrement = height+periodyspace

if darkmode:
    mode = style['DarkMode']
else:
    mode = style['LightMode']
saturation = mode['Saturation']
value = mode['Value']
textcolor = mode['TextColour']
tickcolor = mode['TickColour']


# Function for checking overlaps between two time periods
def isOverlap(start1, end1, start2, end2):
    first_inter={
        "starting_time": start1,
        "ending_time": end1
    }
    second_inter={
        "starting_time": start2,
        "ending_time": end2
    }
    for f,s in ((first_inter,second_inter), (second_inter,first_inter)):
        #will check both ways
        for time in (f["starting_time"], f["ending_time"]):
            if s["starting_time"] < time < s["ending_time"]:
                return True
        return False

# Get monitor information
monitors = get_monitors()

# Choose monitor
monitor = monitors[0]
monwid = monitor.width-2*widthreduce

advPrint("Editing image")
with Image.open(sbgpath) as im:

    # Drawn layers: first list is list of layers, nested list is list of periods in that layer
    drawn=[[]]

    # Drawing the UI
    drawIm = ImageDraw.Draw(im)

    # Get the y size of the text for offsets
    textbbox = drawIm.textbbox([0,0], "12:34", font=font)
    textysize = textbbox[3]-textbbox[1]

    # Get base y of periods display
    basey=baseyoffset+longticklength+timelineoffset+textysize+timelinetextoffset

    # Drawing the timeline
    for i in range(int(dayLength.total_seconds()/60)):
        currenttime = dayStart+timedelta(0,i*60)
        posx = round(i/dayLength.total_seconds()*60*monwid+widthreduce)

        # Draw labels and ticks for every x:00 time, if it is at least 10 minutes after and before the end
        if int(currenttime.strftime("%M"))==0:
            if i>=10 and dayLength.total_seconds()/60-i>=10:
                text = datetime.strftime(currenttime, "%H:%M")
                textbbox = drawIm.textbbox([0,0], text, font=font)
                pos = [
                    posx-round(textbbox[2]/2),
                    -textbbox[1]+timelineoffset
                ]
                drawIm.text(pos, text, font=font, fill=textcolor)

                shape = [posx, textysize+timelineoffset+timelinetextoffset, posx, textysize+timelineoffset+longticklength+timelinetextoffset]
                drawIm.line(shape, fill=tickcolor, width=longtickthickness)

        # Draw ticks for every x:x0 time
        noLabelLineMinutes = [10,20,30,40,50]
        if int(currenttime.strftime("%M")) in noLabelLineMinutes and not i==0:
            shape = [posx, timelineoffset+textysize+(longticklength-shortticklength)+timelinetextoffset, posx, timelineoffset+textysize+longticklength+timelinetextoffset]
            drawIm.line(shape, fill=tickcolor, width=shorttickthickness)

    # Draw labels and ticks for the start and end time
    startendtimes = [dayStart, dayFinish]
    for i in range(2):
        currenttime = startendtimes[i]
        posx = round(i/1*monwid+widthreduce)
        shape = [posx, timelineoffset+textysize+timelinetextoffset, posx, timelineoffset+textysize+longticklength+timelinetextoffset]
        drawIm.line(shape, fill=tickcolor, width=longtickthickness)

        text = datetime.strftime(currenttime, "%H:%M")
        textbbox = drawIm.textbbox([0,0], text, font=font)
        if i==0:
            pos = [
                posx,
                -textbbox[1]+timelineoffset
            ]
        if i==1:
            pos = [
                posx-textbbox[2],
                -textbbox[1]+timelineoffset
            ]
        drawIm.text(pos, text, font=font, fill=textcolor)

    # Drawing the periods
    for i in periods:
        # Check for overlaps
        overlap = 0
        for o in range(len(drawn)):
            layer = drawn[o]
            overlapInLayer = False
            for j in layer:
                if isOverlap(i['startdatetime'],i['finishdatetime'],j['startdatetime'],j['finishdatetime']) or (i['startdatetime']==j['startdatetime'] and i['finishdatetime']==j['finishdatetime']):
                    overlapInLayer = True
                    advPrint("Overlap detected between \""+i['title']+"\" and \""+j['title']+"\"")
            # If there is an overlap and the period doesn't have a previous layer where it doesn't overlap
            if overlapInLayer and o==overlap:
                overlap += 1

        # Decide on colour for subject
        if i['title'] in subjectColours:
            colorHSV = (subjectColours[i['title']],saturation,value)
        else:
            hash = hashlib.md5(i['title'].encode('utf8')).digest()[0]
            colorHSV = (hash/255,saturation,value)
        color = hsv_to_rgb(colorHSV[0],colorHSV[1],colorHSV[2])
        color = (round(color[0]*255),round(color[1]*255),round(color[2]*255),255)

        # Draw rectangle to encase text
        shape = [
            i['position'].total_seconds()/dayLength.total_seconds()*monwid+periodxspace/2+widthreduce, #x0, position normalised to display width
            basey+heightIncrement*overlap, #y0
            (i['position'].total_seconds()+i['length'].total_seconds())/dayLength.total_seconds()*monwid-periodxspace/2+widthreduce, #x1 position+length normalised to display width
            basey+height+heightIncrement*overlap #y1
            ] 
        drawIm.rounded_rectangle(shape, fill=color, radius=roundradius)

        # Find if there is a room change (This is not used for anything else, just for checking)
        splitLoc = i['location'].split(";")
        if len(splitLoc)>1:
            advPrint("Room change detected in \""+i['title']+"\"")

        location = i['location']

        # Write text
        text = ""
        disregardLoc = ["unassigned","refer to event description"]
        if not location.lower() in disregardLoc:
            text += location+seperator
        text +=i['title']+seperator+i['starttime']
        if includeTeacher:
            text += seperator+i['teachercode']
        advPrint(text)

        tbbox=drawIm.textbbox([0,0], text, font=font)

        # Cut off letters that go outside the text box
        while drawIm.textbbox([0,0], text, font=font)[2]>(shape[2]-shape[0]-5):
            text=text[:-1]

        pos = [
            shape[0]+7,
            round(((height)/2)+basey-(tbbox[3]+tbbox[1])/2)+heightIncrement*overlap
        ]
        drawIm.text(pos, text, font=font, fill=textcolor)
        
        # Log period as drawn
        if overlap>=len(drawn):
            drawn.append([])
        drawn[overlap].append(i)

    # Save image
    im.save(appdata+'\\tempbg.png', "PNG")
    advPrint("Finished editing image")
    
# Set image as wallpaper
windll.user32.SystemParametersInfoW(20, 0, appdata+'\\tempbg.png', 0)
advPrint("Set image as wallpaper")