#!/usr/local/bin/python3

# Inspired by:
# https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html

# std library
import argparse
import logging
import os
import sys
import threading
import time

# 3rd party modules
import soco
from soco import SoCo

file_handler = logging.FileHandler('track_log.txt', 'a')
formatter = logging.Formatter('%(asctime)s \t %(message)s')
file_handler.setFormatter(formatter)
log = logging.getLogger('mylogger')
log.addHandler(file_handler)
log.setLevel('INFO')

class SonosAntiAbuse(object):
    """
    Main class.
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='sonos_anti_abuse',
            usage='%(prog)s [options]',
            description='Monitors the Sonos queue and skips tracks based on words in their titles.'
            )
        self.parser.add_argument('command', help='Subcommand to run')
        self.subparsers = self.parser.add_subparsers()
        self.monitor_parser = self.subparsers.add_parser(
            'monitor',
            help='Monitors a player on the network'
            )
        self.scanner_parser = self.subparsers.add_parser(
            'scan',
            help='Returns a list of players/ip addresses on the network.'
        )
        args = self.parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
           print('Unrecognized command')
           self.parser.print_help()
           exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def monitor(self):
        """
        Method containing the monitor subcommand.
        """

        self.monitor_parser.add_argument(
            '--players',
            '-p', 
            metavar='<players>', 
            help='The IP address for one players, or a comma separated list of several players. If left empty, all players will be monitored.'
            )
        self.monitor_parser.add_argument(
            '--skipfile_directory',
            '-s',
            metavar='<directory>',
            default='annoying',
            help='Defaults to annoying/. All files inside matching *.annoying will be read.'
            )
        self.monitor_parser.add_argument(
            '--volume_correct',
            '-v',
            metavar='<int>',
            type=int,
            help='This will turn down the volume if over the specified value.'
        )
        args = self.monitor_parser.parse_args(sys.argv[2:])

        self.skip_list = generate_skip_list(args.skipfile_directory)
        self.players = generate_player_list(args.players)
        self.volume_correct = args.volume_correct
        self.skipfile_directory = args.skipfile_directory

        return track_monitor(
            self.players, 
            self.volume_correct, 
            self.skipfile_directory, 
            self.skip_list
            )

    def scan(self):
        """
        Method containing the scan subcommand.
        """
        if '-h' in sys.argv or '--help' in sys.argv:
            print(sys.argv)
            self.scanner_parser.print_help()
            exit(1)
        self.scanner_parser.parse_args([scanner()])

def title_checker(track: str, skip_list: list) -> bool:
    """
    Compares the track title to skip_list and returns True if a match is found.
    """
    track_name = ''.join(e.lower() for e in track if e.isalnum())
    res = [word for word in skip_list if word in track_name]
    return bool(res)

def scanner():
    """
    Prints IP addresses of players.
    """
    players = soco.discover()
    for player in list(players):
        print(f'{player.ip_address}\t{player.player_name}')
    sys.exit()

def flatten(l: list) -> list:
    return [item for sublist in l for item in sublist]

def generate_player_list(player_list: str) -> set:
    return_set = set()
    if player_list is None:
        return return_set
    for player in player_list.split(','):
        try:
            return_set.add(SoCo(player))
        except ValueError:
            print(f'Error: {player} is not a valid IP address! Run `sonos_anti_abuse scan` to see available players.')
            sys.exit(1)
    return return_set

def generate_skip_list(skipfile_directory: str) -> set:
    """
    Reads the files matching *.annoying in the given directory and outputs an escaped list of strings.
    """
    skip_list = set()
    try:
        for f in os.listdir(skipfile_directory):
            if os.path.isfile(os.path.join(skipfile_directory, f)) and ".annoying" in f:
                with open(f"{skipfile_directory}/{f}", 'r') as skip_file:
                    skip_list.add(word.strip('\n') for word in skip_file.readlines())
    except FileNotFoundError:
        print(f"Directory: {skipfile_directory} not found!")
        sys.exit(1)
    return set(word for word in flatten(skip_list) if word)

def track_monitor(player_list: set, volume_correct: int, skipfile_directory: str, skip_list: set):
    """
    Main function for monitoring the queue.
    """

    threading.Event()
    
    try:
       volume_correct = int(volume_correct)
    except TypeError:
       volume_correct = False

    if not player_list:
        player_list = list(soco.discover())

    threads = []

    print(f"---\n")
    print(f"Starting Sonos Anti Abuse Script on speakers: \n")
    for player in player_list:
        print(f" * {player.player_name}")
    print("\n")
    print("Skipfiles:")
    print(f"{skipfile_directory}/")
    for f in os.listdir(skipfile_directory)[:-1]:
        if os.path.isfile(os.path.join(skipfile_directory, f)) and ".annoying" in f:
            print(f" ├── {f}")
    print(f" └── {os.listdir(skipfile_directory)[-1]} ")
    print("\n")
    print("Quit with CTRL+C")
    print(f"---\n")
    
    try:
        for player in player_list:
            x = threading.Thread(
                target=track_skipper, 
                args=(player, skip_list,), 
                kwargs={'volume_correct' : volume_correct}
            )
            threads.append(x)
            x.daemon = True
            x.start()
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print(f"\n Exiting.")
        sys.exit()      

def track_skipper(player: soco.core.SoCo, skiplist: set, skip_mode: str="title", volume_correct: bool=False) -> None:
    """
    This function contains the logic for which track to skip and when.
    """
    track_title = ""
    transport_state = ""
    # These two needs to have a different value than their counterparts above
    # so that the while loop can start properly.
    old_track_title = "placeholder"
    old_transport_state = "placeholder"
    
    while True:
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
        #   track_length = datetime.datetime.strptime(track_info['duration'], '%H:%M:%S').time()
        #   track_position = datetime.datetime.strptime(track_info['position'], '%H:%M:%S').time()

        track_str = f'{player.player_name}\t{track_artist}\t{track_title}'
        transport_state = player.get_current_transport_info()['current_transport_state']
        logstr = ''
        
        if old_transport_state != transport_state or old_track_title != track_title:
            print(f'{track_str}\t{transport_state}')
            
            ## I may implement other "modes" in the future
            if skip_mode == 'title':
                if old_track_title != track_title:
                    track_skip = title_checker(track_info['title'], skiplist)
            else:
                track_skip = False
            
            if track_skip:
                # The player throws an error when trying to skip the last track in the queue,
                # so we catch that error and stop the track instead.
                try:
                    player.next()
                    logstr = f"{track_str} \t SKIPPED"
                    print(logstr)
                except soco.exceptions.SoCoUPnPException:
                    player.stop()
                    logstr = f"{track_str} \t STOPPED"
            else:
                logstr = f"{track_str} \t PLAYED"

        if volume_correct and volume_correct < player.volume:
            player.volume = volume_correct
            print(f"{track_str} \t VOLUME CORRECTED")
            logstr = f"{track_str} \t VOLUME CORRECTED"

        if logstr:
            log.info('%s', logstr)
        
        old_transport_state = transport_state
        old_track_title = track_title
        time.sleep(2)

if __name__ == '__main__':
    SonosAntiAbuse()