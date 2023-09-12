import platform
system = platform.system()
if system == "Linux":
    from os import environ
    desktop_session = environ.get("DESKTOP_SESSION")
    print("Detected "+system+" with "+desktop_session)
else:
    print("Detected "+system)
# Main CompassBG script
from datetime import datetime, timedelta
codeInitTime = datetime.now()

# Print but with timestamps and stuff
def advPrint(string):
    timeUntilNow = (datetime.now()-codeInitTime)
    timestr = '['+str(round(timeUntilNow.total_seconds(),3))+'s]'
    if len(timestr) < 8:
        printstr = timestr+':  '+string
    else:
        printstr = timestr+': '+string
    print(printstr)

print("")
advPrint("Loading liblaries")
import compass as compass
import multiprocessing as mp # For parallel compass requests
from requests_toolbelt import sessions
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
if system == "Windows":
    from ctypes import windll
if system == "Linux":
    import kwall
import math


# Paths
scriptLoc = path.dirname(path.realpath(__file__)).replace(("\\"), ("/"))
HOME = str(Path.home()).replace(("\\"), ("/"))
if system == "Windows":
    appdata = getenv('LOCALAPPDATA').replace(("\\"), ("/")) + '/Azimuth'
if system == "Linux":
    appdata = HOME+"/.config/azimuth"
bgpath = HOME.replace(("\\"), ("/"))+"/Pictures/Azimuth"

# Print versions
print("")
advPrint("File Versions: ")
with open(scriptLoc+"/azimuth.version","r") as version:
    advPrint("  Azimuth v"+version.read())
with open(appdata+"/pref.json","r") as pref:
    advPrint("  Preferences file for v"+load(pref)['Version'])
with open(appdata+"/cfg.json","r") as config:
    advPrint("  Config file for v"+load(config)['version'])
with open(appdata+"/style.json","r") as style:
    style = load(style)
    advPrint("  \""+style['Name']+"\" style by "+style["Author"]+" for v"+style['Version'])

# Wait for internet connection
print("")
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
tempCfg = load(open(appdata + "/cfg.json", 'r'))
# Change the names of keys so the code doesn't break
tempCfg = translateDict(tempCfg, "code")
# Convert dictionary to namespace 
cfg = SimpleNamespace(**tempCfg)

# Select background from folder
if len(listdir(bgpath)) == 0:
    print("")
    advPrint("[WARNING] There are no background images in the directory at: \n"+bgpath+"\n, please put one or more in there.")
    sleep(5)
    exit()
bgs = []
for file in listdir(bgpath):
    if file.endswith(".png") or file.endswith(".jpg"):
        bgs.append(file)
sbgpath = bgpath+"/"+bgs[randint(0, len(bgs)-1)]

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
# todayDate = "2023-05-14"
print("")
advPrint("Date: "+todayDate)

def parallel_get_lessons_by_instance_id(instanceId):
    global tempCfg 
    s = sessions.BaseUrlSession(base_url="https://"+tempCfg["schoolcode"]+".compass.education/services/")
    s.cookies.set("ASP.NET_SessionId", tempCfg["sessionid"])
    s.headers={"Accept": "*/*", "Content-Type": "application/json", "Accept-Encoding": "gzip, deflate", "User-Agent": "iOS/14_6_0 type/iPhone CompassEducation/6.3.0", "Accept-Language": "en-au", "Connection": "close"}
    data = {"instanceId": instanceId}
    return s.post('Activity.svc/GetLessonsByInstanceId',json=data).json()['d']

def getPeriods(sessionid, schoolcode):
    advPrint("Authenticating with Compass")
    c = compass.CompassAPI(sessionid, schoolcode)
    advPrint("Getting events list")
    events = c.get_calender_events_by_user(todayDate)

    # Pararellised requests to compass
    advPrint("Getting lesson infos for each lesson")
    instanceids=[ period["instanceId"] for period in events ] # Get instance ids of each event
    pool=mp.Pool(mp.cpu_count())
    mplessons=pool.map(parallel_get_lessons_by_instance_id, instanceids)
    pool.close()

    periods = []
    for eindex, period in enumerate(events):
        periodInfo = {}
        periodInfo["title"]=period["title"]
        periodInfo["starttime"]=period["start"]
        periodInfo["finishtime"]=period["finish"]

        instanceId=period["instanceId"]
        lessons = mplessons[eindex]
        periodInfo["instanceId"]=instanceId
        
        lessonInstanceId=0
        for i in range(len(lessons['Instances'])):
            lessonInstance = lessons['Instances'][i]
            if lessonInstance['st'] == period["start"]:
                lessonInstanceId=i
            
        CoveringIid = lessons['Instances'][lessonInstanceId]['CoveringIid']
        if CoveringIid == None:
            periodInfo['teachercode']=lessons['Instances'][lessonInstanceId]['m']
            periodInfo['teachersubstitute']=False
        else:
            periodInfo['teachercode']=CoveringIid
            periodInfo['teachersubstitute']=True
        ld = lessons['Instances'][lessonInstanceId]['LocationDetails']
        if ld==None:
            periodInfo['location']="none"
        else:
            periodInfo['location']=ld['shortName']

        periods.append(periodInfo)
    return periods

    
(sessionid, schoolcode)=(cfg.sessionid, cfg.schoolcode)

periods = getPeriods(sessionid, schoolcode)

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


def CrossPlatformSetWallpaper(multimonitor, location, desktop="all"):
    multimonitor = multimonitor.lower()
    if multimonitor == "unsupported" or multimonitor == "both":
        if system == "Windows":
            advPrint("Using windll to set wallpaper")
            windll.user32.SystemParametersInfoW(20, 0, appdata+'/tempbg'+str(desktop)+'.png', 0)
            advPrint("Set image as wallpaper")

    if multimonitor == "supported" or multimonitor == "both":
        if system == "Linux":
            if desktop_session == "plasma" or desktop_session == "plasmawayland":
                advPrint("Using plasma dbus interface to set wallpaper for desktop "+str(desktop))
                kw = kwall.KWallAPI()
                kw.setwallpaper(sbgpath, desktop=desktop) # To refresh wallpaper
                kw.setwallpaper(appdata+'/tempbg'+str(desktop)+'.png',desktop=desktop)
                advPrint("Set image as wallpaper for desktop "+str(desktop))

# Check that there are events scheduled
if dayLength == 0:
    advPrint("There are no scheduled events today")

    # If no events are scheduled, set empty image as wallpaper
    CrossPlatformSetWallpaper(multimonitor="both", location=sbgpath)
    # if system == "Windows":
    #     advPrint("Using windll to set wallpaper")
    #     windll.user32.SystemParametersInfoW(20, 0, sbgpath, 0)
    # if system == "Linux":
    #     if desktop_session == "plasma":
    #         advPrint("Using plasma dbus interface to set wallpaper")
    #         kw = kwall.KWallAPI()
    #         kw.setwallpaper(appdata+'/tempbg.png') # To refresh wallpaper
    #         kw.setwallpaper(sbgpath)
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

# Import files
pref=load(open(appdata+"/pref.json"))
subjectColours=pref['SubjectColours']
darkmode=pref['Darkmode']
includeTeacher=pref['IncludeTeacher']

style=load(open(appdata+"/style.json")) 
seperator=style['Seperator']                        # The character used to seperate properties in the period display
timelineoffset = style['TimelineOffset']                # How much the timeline is offset from the top of the display
timelinetextoffset = style['TimelineTextOffset']             # How much the timeline is offset from the timeline text
baseyoffset = style['BaseYOffset']                          # How much the period display is offset from the timeline
height = style['Height']                                                                      # Height of each period
periodyspace = style['PeriodYSpace']                                    # Space between periods when they are stacked
periodxspace = style['PeriodXSpace']                                  # Amount to subtract from the width of a period
widthreduce = style['WidthReduce']                        # Double the space between the edge of the display to the UI
longticklength = style['LongTickLength']            # Length of the long ticks
longtickthickness = style['LongTickThickness']      # Thickness of the long ticks
shortticklength = style['ShortTickLength']          # Length of the short ticks
shorttickthickness = style['ShortTickThickness']    # Thickness of the short ticks
roundradius = style['RoundRadius']                  # Radius of squares for periods
fontsize = style['FontSize']                        # Size of text

font=ImageFont.truetype(scriptLoc+"/Inter-SemiBold.otf", size=fontsize)
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

def softresize(im, size, originalsize):
    # Find the resize ratio
    ratio = [1,1]
    for i in range(2):
        ratio[i] = size[i]/originalsize[i]

    # Resize image size
    resizesize=[0,0]
    for i in range(2):
        resizesize[i]=round(originalsize[i]*max(ratio))
    im=im.resize(tuple(resizesize),resample=Image.LANCZOS)

    # Crop image
    (left, upper, right, lower) = (
        math.floor((resizesize[0]-size[0])/2), 
        math.floor((resizesize[1]-size[1])/2), 
        resizesize[0]-math.ceil((resizesize[0]-size[0])/2), 
        resizesize[1]-math.ceil((resizesize[1]-size[1])/2)
        )
    im = im.crop((left, upper, right, lower))
    return im

# Get monitor information
monitors = get_monitors()

# Choose monitor
if system == "Linux" and (desktop_session == "plasma" or desktop_session == "plasmawayland"):
    iteratetimes = len(monitors)
elif system == "Windows":
    iteratetimes = 1
    if len(monitors)>1:
        advPrint("Multi monitor support is not avaiable on Windows, the wallpaper will be created using the resolution of the primary monitor and set to all screens")
else:
    iteratetimes = 0
    sysexit()

# Messages to be saved for later
messagesForLater = []

for mon in range(iteratetimes):
    print("")
    advPrint("Iteration "+str(mon))
    monitor = monitors[mon]
    monwid = monitor.width-2*widthreduce

    advPrint("Editing image "+str(mon))
    with Image.open(sbgpath) as im:
        im = softresize(im, (monitor.width, monitor.height), im.size)

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
                        if mon==0:
                            messagesForLater.append("Overlap detected between \""+i['title']+"\" and \""+j['title']+"\"")
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
            location = i['location']

            # Write text
            text = ""
            disregardLoc = ["unassigned","refer to event description", "none"]
            if not location.lower() in disregardLoc:
                text += location+seperator
            else:
                if mon==0:
                    messagesForLater.append("No location found for \""+i['title']+"\"")
            text +=i['title']+seperator+i['starttime']
            if includeTeacher:
                text += seperator+i['teachercode']
            if mon==0:
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
        im.save(appdata+'/tempbg'+str(mon)+'.png', "PNG")
        advPrint("Finished editing image "+str(mon))

        # Set image as wallpaper
        CrossPlatformSetWallpaper(multimonitor="both", location=appdata+'/tempbg'+str(mon)+'.png', desktop=mon)
        # if system == "Windows":
        #     advPrint("Using windll to set wallpaper")
        #     windll.user32.SystemParametersInfoW(20, 0, appdata+'/tempbg'+str(mon)+'.png', 0)
        #     advPrint("Set image as wallpaper")

        # if system == "Linux":
        #     if desktop_session == "plasma" or desktop_session == "plasmawayland":
        #         advPrint("Using plasma dbus interface to set wallpaper for desktop "+str(mon))
        #         kw = kwall.KWallAPI()
        #         kw.setwallpaper(sbgpath, desktop=mon) # To refresh wallpaper
        #         kw.setwallpaper(appdata+'/tempbg'+str(mon)+'.png',desktop=mon)
        #         advPrint("Set image as wallpaper for desktop "+str(mon))

for i in periods:
    # Find if there is a room change (This is not used for anything else, just for checking)
    splitLoc = i['location'].split(";")
    if len(splitLoc)>1:
        advPrint("Room change detected in \""+i['title']+"\"")
        
    # Find if there is a subsitute teacher (This is not used for anything else, just for checking)
    if i['teachersubstitute']:
        advPrint("Substitute teacher detected in \""+i['title']+"\"")

for i in messagesForLater:
    advPrint(i)
