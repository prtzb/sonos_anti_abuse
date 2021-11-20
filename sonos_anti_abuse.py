# Inspired by:
# https://mike.depalatis.net/blog/simplifying-argparse.html

import argparse
import soco
from soco import SoCo
import threading
import time
import csv
import datetime
import logging
import sys
#import getopt
import re

file_handler = logging.FileHandler('track_log.txt', 'a')
formatter = logging.Formatter('%(asctime)s \t %(message)s')
file_handler.setFormatter(formatter)
log = logging.getLogger('mylogger')
log.addHandler(file_handler)
log.setLevel('INFO')

# my_parser = argparse.ArgumentParser(
#     prog='sonos_anti_abuse',
#     usage='%(prog)s [options]',
#     description='Monitors the Sonos queue and skips tracks based on words in their titles.'
#     )

#my_parser.add_argument(
#    '--host',
#    help='The IP address of the player you want to monitor, or "all" for every player on the network.',
#)

# my_parser.add_argument(
#     '--wordfile',
#     '-w',
#     default='annoying.txt',
#     help='Defaults to annoying.txt, but this can be whatever file you want. Just put each keyword on a new line.'
# )

# my_parser.add_argument(
#     '--volume_correct',
#     '-v',
#     action='store_true',
#     help='This will turn down the volume if it is over 75.'
# )


# subparsers = my_parser.add_subparsers(dest='subcommand')

# parser_monitor = subparsers.add_parser(
#     'monitor',
#     help='Select IP to monitor, or "all" for all players on the network.'
# )

# parser_monitor.add_argument(
#     'host',
#     help='host'
# )

# parser_monitor.add_argument(
#     '--wordfile',
#     '-w',
#     default='annoying.txt',
#     help='Defaults to annoying.txt, but this can be whatever file you want. Just put each keyword on a new line.'
# )


# parser_scanner = subparsers.add_parser(
#     'scan',
#     help='Returns the IP addresses of all players on the network.'
# )

# my_args = vars(my_parser.parse_args())

# def subcommand(args=[], parent=subparsers):
#     def decorator(func):
#         parser = parent.add_parser(func.__name__, description=func.__doc__)
#         for arg in args:
#             parser.add_argument(*arg[0], **arg[1])
#         parser.set_defaults(func=func)
#     return decorator

# def argument(*name_or_flags, **kwargs):
#     return ([*name_or_flags], kwargs)

# @subcommand([argument("name", help="Name")])
# def name(args):
#     print(args.name)#

class SonosAntiAbuse(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            prog='sonos_anti_abuse',
            usage='%(prog)s [options]',
            description='Monitors the Sonos queue and skips tracks based on words in their titles.'
            )
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def monitor(self):
        parser = argparse.ArgumentParser(
            'monitor',
            description='Monitors a player on the network'
            )
        parser.add_argument(
            'player', 
            metavar='<player>', 
            help='The IP address for a player, or "all" every player on the network'
            )
        parser.add_argument(
            '--wordfile',
            '-w',
            default='annoying.txt',
            help='Defaults to annoying.txt, but this can be whatever file you want. Just put each keyword on a new line.'
            )
        parser.add_argument(
            '--volume_correct',
            '-v',
            action='store_true',
            help='This will turn down the volume if it is over 75.'
        )

        args = parser.parse_args(sys.argv[2:])
        print(args)
        #print('Running on host ' + args.player)



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



#@subcommand()
def scan(args):
    """
    Prints IP addresses of players.
    """
    players = discover_extended()
    for player in players:
        print(player + "\t" + players[player])
    sys.exit()

#@subcommand()
def monitor(argv):

    print(argv)
    event = threading.Event()

    wordfile = argv.wordfile
    host = argv.player
    volume_correct = argv.volume_correct

    try:
        file = open(wordfile, 'r')
        skip_list = [word.strip('\n') for word in file.readlines()]
    except FileNotFoundError:
        print("File: " + wordfile + " not found!")
        sys.exit()

    #if not host:
    #    print("Please specify a valid hostname/ip with --host")
    #    sys.exit()
    if host == "all":
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
                    kwargs={'volume_correct' : volume_correct}
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
        print(" * " + soco.SoCo(host.player_name)
        print("Quit with CTRL+C")
        print("---" + "\n")
        try:
            track_skipper(
                soco.SoCo(my_args['host']), 
                skip_list, 
                volume_correct=my_args['volume_correct']
            )
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
        #   track_length = datetime.datetime.strptime(track_info['duration'], '%H:%M:%S').time()
        #   track_position = datetime.datetime.strptime(track_info['position'], '%H:%M:%S').time()
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

if __name__ == '__main__':
    SonosAntiAbuse()

