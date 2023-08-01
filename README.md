# Azimuth
## A simple script to set your compass schedule as your Windows wallpaper
A rewrite of CompassBG, with a more reliable script and a nicer UI

## BROKEN as of 2023-07-30, due to the change in Compass' API. I'll try to adapt the code to work with the new API, but no promises.

![image](https://user-images.githubusercontent.com/73152770/228744545-03d33a4e-afdd-498a-83c4-9cd9bf1ed2eb.png)

I haven't written a port for linux **yet**. It's only available on Windows.

Step 0:
 Download the latest release of Azimuth from the "Releases" section of this github

Step 1:
	Place the Azimuth folder in your preferred location
	(The optional task scheduler thing will break if the Azimuth directory is moved)

Step 2:
	Create a configuration file by running azimuthsetup.exe manually
	This will create a Azimuth directory in Appdata with configuration files inside it

Step 3:
 Add wallpaper images (with the resolution of the main display) into Pictures\Azimuth

Step 4 (Optional):
	Set up azimuthw.exe (no console version) to run at startup through Task Scheduler
  
  Task scheduler can be found by searching for it in the windows menu. If you aren't comfortable with this, look up a tutorial! It's a very useful program to know.
		
		(My settings for Task Scheduler)
		Triggers:
			At log on of any user
		Action: 
			Start a program: Program/Script: "C:\(put the location of the Azimuth folder here)\compassbgw.exe"
		Conditions:
			None
  
  Make sure to turn off the "only run when connected to AC power" setting!

## Other instructions

To edit settings or create the settings file manually:
	Run azimuthsetup.exe

## Troubleshooting

If your background isn't being set:
	Try setting some background image as wallpaper through file explorer
	
	Run azimuth.exe manually through windows powershell by:
	1. Shift right click in the file explorer folder containing azimuth.exe
	2. Click on "Open powershell window here"
	3. Type ".\\azimuth.exe"
	4. Press enter
	This should give you an error message. Try looking it up on google, or make a "new issue" in this github about it.
