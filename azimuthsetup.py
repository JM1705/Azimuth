import platform
system = platform.system()
print("Detected "+system)
from pathlib import Path
from os import getenv, path, listdir
from json import load, dump
from getpass import getpass
from time import sleep

def yntobool(yn, default):
    boolean = default
    yn = yn.lower()
    if yn == "y":
        boolean = True
    if yn == "n":
        boolean = False
    return boolean

# Paths
scriptLoc = path.dirname(path.realpath(__file__)).replace(("\\"), ("/"))
HOME = str(Path.home()).replace(("\\"), ("/"))
if system == "Windows":
    appdata = getenv('LOCALAPPDATA').replace(("\\"), ("/")) + '/Azimuth'
if system == "Linux":
    appdata = HOME+"/.config/azimuth"
bgpath = HOME.replace(("\\"), ("/"))+"/Pictures/Azimuth"

# Constant
version = open(scriptLoc.replace(("\\"), ("/"))+"/azimuth.version","r").read()

# Create directories if they do not exist
createPaths = [bgpath, appdata]
pathstitle = ["backgrounds folder", "appdata folder"]
for i in range(len(createPaths)):
    if path.exists(createPaths[i]):
        print("Not creating the Azimuth "+pathstitle[i]+" at "+createPaths[i]+" as it already exists")
    else:
        print("Created the Azimuth "+pathstitle[i]+" at "+createPaths[i])
        Path(createPaths[i]).mkdir(parents=True, exist_ok=True)

# Check if to create configuration file
cfgLoc = appdata+"/cfg.json"
if path.isfile(cfgLoc):
    try:
        cfg = load(open(cfgLoc, "r"))
        createcfg = input("Config file already exits at "+cfgLoc+" of version v"+cfg['version']+", do you want to rewrite this? (y(default),n) ")
        createcfg = yntobool(createcfg, True)
    except:
        print("The configuration file at "+cfgLoc+" could not be loaded, we will rewrite this file now")
        createcfg = True
else:
    print("The configuration file at "+cfgLoc+" was not found, we will create this file now")
    createcfg = True

# Create configuration file
if createcfg == True:
    print("")
    print("Enter your school code. This is the part in your compass URL between")
    print("https://")
    print("and")
    print("compass.education")
    schoolcode = input("School code: ")

    print("")
    print("Enter your compass login token. For a guide on how to obtain this, visit https://github.com/JM1705/Azimuth/blob/main/README.md")
    token = input("Compass login token: ")

    cfg = {
        "version": version,
        "sessionid": token,
        "school_code": schoolcode
    }
    dump(cfg, open(cfgLoc, 'w'), indent = '\t')
    print("")
    print("Wrote configuration file at "+cfgLoc)

# Check if to create styles file
print("")
styleLoc = appdata+"/style.json"
if path.isfile(styleLoc):
    try:
        style = load(open(styleLoc, "r"))
        createstyle = input("Style file already exits at "+styleLoc+" of version v"+style['Version']+", do you want to rewrite this? (y(default),n) ")
        createstyle = yntobool(createstyle, True)
    except:
        print("The style file at "+styleLoc+" could not be loaded, we will rewrite this file now")
        createstyle = True
else:
    print("The style file at "+styleLoc+" was not found, we will create this file now")
    createstyle = True

if createstyle:
    print("")
    style = load(open(scriptLoc+"/defaultstyle.json", "r"))
    style['Version']=version
    dump(style, open(styleLoc, 'w'), indent = '\t')
    print("")
    print("Wrote style file at "+styleLoc)


# Check if to create preferences file
print("")
prefLoc = appdata+"/pref.json"
if path.isfile(prefLoc):
    try:
        pref = load(open(prefLoc, "r"))
        createPrefs = input("Preferences file already exits at "+prefLoc+" of version v"+pref['Version']+", do you want to rewrite this? (y(default),n) ")
        createPrefs = yntobool(createPrefs, True)
    except:
        print("The Preferences file at "+prefLoc+" could not be loaded, we will rewrite this file now")
        createPrefs = True
else:
    print("The Preferences file at "+prefLoc+" was not found, we will create this file now")
    createPrefs = True

# Create preferences file
if createPrefs:
    print("")
    pref = load(open(scriptLoc+"/defaultpref.json", "r"))
    pref["Version"]=version
    pref["Darkmode"]=yntobool(input("Use dark mode? (y(default),n) "),True)
    pref["IncludeTeacher"]=yntobool(input("Include teacher code in the UI? (y(default),n) "),True)
    pref['Version']=version
    dump(pref, open(prefLoc, 'w'), indent = '\t')
    print("")
    print("Wrote preferences file at "+prefLoc)

# Select background from folder
if len(listdir(bgpath)) == 0:
    print("There are no background images in the directory at "+bgpath+", please put one or more in there.")
    sleep(5)
    
print("Setup completed.")
print("Now, please place background images in the directory at "+bgpath)
sleep(7)
exit()