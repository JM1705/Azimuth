# A guide on obtaining the Compass login token
## Warning, I haven't been able to find a way to deauthorise a token, so if someone takes your token they might have access to your Compass account forever.
1. Log into compass on a web browser
2. Open Developer tools on Compass (Ctrl+Shift+I on Firefox)
3. Open the Network tab, and click "Reload". You should see a list of requests.
4. Find the request for "GetCalendarEventsByUser", and click on it.
5. In the "Cookies" tab of the request, you should see a "ASP.NET_SessionId" field. This is your Compass login token. 
