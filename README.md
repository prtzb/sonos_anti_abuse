# sonos_anti_abuse
This is a script that monitors Sonos speakers and skips tracks automatically.

***Basic usage:*** 
    
    --host      	Ip/hostname of player. If you pass "all", the script will monitor 
			every player in your network.
    --wordfile  	Defaults to annoying.txt, but this can be whatever file you want. 
                	Just put each keyword on a new line.
    --scan          	Finds the players and their IPs in your network.
    --volume_correct    This will turn down the volume if it's over 75.  
    

Example 1:
      

`python3 sonos_track_check.py --host 192.168.0.2`


Example 2:      


`python3 sonos_track_check.py --host all --wordfile christmas.txt`


Example 3:      


`python3 sonos_track_check.py --host all --volume_correct` 
