# Script used by azimuth.py and azimuthsetup.py to convert key names in the json dictionary to variable names because I'm too lazy for long variable names
def translateDict(dict, to):
    keyChanges = [
        ["user", "unm"],
        ["pass", "pwd"],
        ["school_code", "schoolcode"]
    ]

    to = to.lower()

    if to == "file":
        for i in keyChanges:
            dict[i[0]] = dict.pop(i[1])

    if to == "code":
        for i in keyChanges:
            dict[i[1]] = dict.pop(i[0])
    
    return dict