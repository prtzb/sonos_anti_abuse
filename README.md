# sonos_anti_abuse
A simple script that monitors Sonos speakers and skips annoying tracks automatically. This is achieved by checking the track title and comparing it to the contents in annoying.txt. If any words in the title match any word in the file, the track is skipped. You can edit annoying.txt and add any words you want to monitor, or simply use your own file with the --wordfile switch.


## Basic usage

    sonos_anti_abuse
    
        monitor                             Ip/hostname of player. If you pass "all", the script will monitor every player in your network.

            -w, -wordfile <file>            Defaults to annoying.txt, but this can be whatever file you want. Just put each keyword on a new line.

            -v, --volume_correct <int>      This will turn down the volume if it's over 75.

        scan                                This will print all players on the network with IP addresses.


Example 1:
      

`python3 sonos_anti_abuse.py monitor 192.168.0.2`


Example 2:      


`python3 sonos_anti_abuse.py monitor all --wordfile christmas.txt`


Example 3:      


`python3 sonos_anti_abuse.py monitor all --volume_correct` 


## Docker

*Note: This will only work on Linux (not Docker Desktop on Windows or macOS). This is because the container needs direct access to the local network with --network=host. Reference: https://docs.docker.com/network/host/*


### Instructions

First, prepare your annoying.txt file and put it under `/configs/sonos_anti_abuse` (or anywhere really, just remember to edit the docker run command below).


Build the image:


`sudo docker build -t sonos_anti_abuse .`


Start the container:


`sudo docker run -dit --name sonos_anti_abuse --network=host -v /configs/sonos_anti_abuse:/config sonos_anti_abuse`


To see what songs have been skipped, you can check the logs like this:


`sudo docker logs sonos_anti_abuse`


If you want to watch the monitor in real time, run this:


`sudo docker attach sonos_anti_abuse`
