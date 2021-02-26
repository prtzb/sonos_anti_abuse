import soco
from soco import SoCo
import threading
import time
import csv
import datetime
import logging
import sys
import getopt
import re

file_handler = logging.FileHandler('track_log.txt', 'a')
formatter = logging.Formatter('%(asctime)s \t %(message)s')
file_handler.setFormatter(formatter)
log = logging.getLogger('mylogger')
log.addHandler(file_handler)
log.setLevel('INFO')

def main(argv):
	event = threading.Event()
	host = ""
	hosts = []
	wordlist = "annoying.txt"
	volume_correct_state = False	
	helper = """
	sonos_anti_abuse.py basic usage: 
	
	--host 			Ip/hostname of player. If you pass "all", the script will monitor 
				every player in your network.
	--wordfile 		Defaults to annoying.txt, but this can be whatever file you want. 
				Just put each keyword on a new line.
	--scan  		Finds the players and their IPs in your network.
	--volume_correct	This will turn down the volume if it's over 75.  
	
	Example 1: 		python3 sonos_track_check.py --host 192.168.0.2
	Example 2: 		python3 sonos_track_check.py --host all --wordfile christmas.txt
	Example 3:		python3 sonos_track_check.py --host all --volume_correct

	"""

	try:
		opts, args = getopt.getopt(argv, "", ["help", "host=", "wordfile=", "scan", "volume_correct"])
	except getopt.GetoptError:
		print(helper)
		sys.exit(2)

	for opt, arg in opts:
		if opt == '--help':
			print(helper)
			sys.exit()
		elif opt == '--host':
			host = arg
		elif opt == '--wordfile':
			wordlist = arg
		elif opt == '--volume_correct':
			volume_correct_state = True
		elif opt == '--scan':
			players = discover_extended()
			for player in players:
				print(player + "\t" + players[player])
			sys.exit()
	try:
		file = open(wordlist, 'r')
		skip_list = [word.strip('\n') for word in file.readlines()]
	except FileNotFoundError:
		print("File: " + wordlist + " not found!")
		sys.exit()

	if not host:
		print("Please specify a valid hostname/ip with --host")
		sys.exit()
	elif host == "all":
		threads = []
		print("---" + "\n")
		print("Starting Sonos Anti Abuse Script on speakers:" + "\n")
		players = list(soco.discover())
		for player in players:
			print(" * " + player.player_name)
		print("Quit with CTRL+C")
		print("---" + "\n")
		try:
			for player in players:		
				x = threading.Thread(
					target=track_skipper, 
					args=(player, skip_list,), 
					kwargs={'volume_correct' : volume_correct_state}
				)
				threads.append(x)
				x.daemon = True
				x.start()
			for thread in threads:
				thread.join()
		except KeyboardInterrupt:
				print("\n" + "Exiting.")
				sys.exit()		
	else:
		print("---" + "\n")
		print("Starting Sonos Anti Abuse Script on speakers:" + "\n")
		print(" * " + soco.SoCo(host).player_name)
		print("Quit with CTRL+C")
		print("---" + "\n")
		try:
			track_skipper(
				soco.SoCo(host), 
				skip_list, 
				volume_correct=volume_correct_state)
		except KeyboardInterrupt:
			print("\n" + "Exiting.")
			sys.exit()
		except ValueError:
			print("Please specify a valid hostname/ip with --host")
			sys.exit()

def track_skipper(player, skiplist, skip_mode="title", volume_correct=False):
	track_title = ""
	transport_state = ""
	# These two needs to have a different value than their counterparts above
    # so that the while loop can start properly.
	old_track_title = "placeholder"
	old_transport_state = "placeholder"

	while True:
		player = player
		try:
			track_info = player.get_current_track_info()
		except:
			print("Lost connection, trying again.")
			time.sleep(5)
			continue
		track_artist = track_info['artist']
		track_title = track_info['title']
		## Not used
		# if track_info['duration'] != "NOT_IMPLEMENTED":
		#	track_length = datetime.datetime.strptime(track_info['duration'], '%H:%M:%S').time()
		#	track_position = datetime.datetime.strptime(track_info['position'], '%H:%M:%S').time()
		track_str = str(
            player.player_name + "\t" + track_artist + "\t" + track_title
        )
		transport_state = player.get_current_transport_info()['current_transport_state']
		logstr = ''
		#status_change = False
		
		if old_transport_state != transport_state or old_track_title != track_title:
			print(track_str + "\t" + transport_state)
			
			## I may implement other "modes" in the future
			if skip_mode == "title":
				if old_track_title != track_title:
					track_skip = title_checker(track_info['title'], skiplist)
			else:
				track_skip = False
			
			if track_skip:
                # The player throws an error when trying to skip the last track in the queue,
                # so we catch that error and stop the track instead.
				try:
					player.next()
					logstr = track_str + "\t" + "SKIPPED"
					print(logstr)
				except soco.exceptions.SoCoUPnPException:
					player.stop()
					logstr = track_str + "\t" + "STOPPED"
			else:
				logstr = track_str + "\t" + "PLAYED"

		if volume_correct and player.volume > 60:
			player.volume = 30
			print(track_str + "\t" + "VOLUME CORRECTED")
			logstr = track_str + "\t" + "VOLUME CORRECTED"
	
		if logstr:
			log.info('%s', logstr)
		
		old_transport_state = transport_state
		old_track_title = track_title
		time.sleep(2)

def title_checker(track, skip_list):
	## Using .isalnum()
	track_name = ''.join(e.lower() for e in track if e.isalnum())
	res = [word for word in skip_list if word in track_name]
	return bool(res)

def discover_extended():
	""" 
	I couldn't find a function in SoCo of returning the IP of a player
	so I had to write this.
	"""
	players = {}
	for player in list(soco.discover()):
		ip = str(player).split()[4].strip(">")
		players.update({ ip : player.player_name })
	return players
	

if __name__ == "__main__":	
	main(sys.argv[1:])

