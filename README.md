# sonos_anti_abuse
A simple script that monitors Sonos speakers and skips annoying tracks automatically. This is achieved by checking the track title and comparing it to the contents in annoying.txt. If any words in the title match any word in the file, the track is skipped.You can edit annoying.txt and add any words you want to monitor, or simply use your own file with the --wordfile switch.


***Basic usage:*** 
    
    --host      		Ip/hostname of player. If you pass "all", the script will monitor 
				every player in your network.
    --wordfile  		Defaults to annoying.txt, but this can be whatever file you want. 
                		Just put each keyword on a new line.
    --scan          		Finds the players and their IPs in your network.
    --volume_correct    	This will turn down the volume if it's over 75.  
    

Example 1:
      

`python3 sonos_anti_abuse.py --host 192.168.0.2`


Example 2:      


`python3 sonos_anti_abuse.py --host all --wordfile christmas.txt`


Example 3:      


`python3 sonos_anti_abuse.py --host all --volume_correct` 
