@echo off
netsh wlan set hostednetwork mode=allow ssid=OfflineEdu key=yourpassword
netsh wlan start hostednetwork
pause