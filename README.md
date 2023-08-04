# Sonos Anti Abuse

Do you have annoying siblings/friends/co-workers who puts stupid songs in your Sonos queue? Or are you like me a hip-hop fan who's just not interested in acapella versions, skits and other tracks that rappers like to put on their albums? Then, this is the script for you!

`sonos_anti_abuse` is a simple script written in Python that monitors Sonos speakers and skips annoying tracks automatically. This is achieved by checking the track title and comparing it to the contents in text files that you define. If any words in the title match any word in one of the files, the track is skipped. You can create your own text files and add any words you want to monitor.


## Basic usage

    sonos_anti_abuse
    
        monitor <ip>                            Ip/hostname of player. If you pass "all", the script will monitor every player in your network.

            -w, --wordfile <file>                Defaults to annoying.txt, but this can be whatever file you want. Just put each keyword on a new line.

            -v, --volume_correct <int>          This will turn down the volume if it's over the passed value.

        scan                                    This will print all players on the network with IP addresses.


Example 1:
      

```bash
python3 sonos_anti_abuse.py monitor 192.168.0.2
```


Example 2:      


```bash
python3 sonos_anti_abuse.py monitor --skipfile_directory ~/my_skipfiles
```


Example 3:      


```bash
python3 sonos_anti_abuse.py monitor --volume_correct 70` 
```


## Skipfiles

Skipfiles contains words that the monitor should look for in song titles. The following formatting rules apply:

- A skipfile filename must always end with the suffix `.annoying`.
- One word per line.

Refer to the files in the `./annoying` subdirectory for examples.

The skipfile path can be controlled with the `--skipfile_directory` switch.


## Docker

*Note: This will only work on Linux (not Docker Desktop on Windows or macOS). This is because the container needs direct access to the local network with --network=host. Reference: https://docs.docker.com/network/host/*

### Instructions Docker Compose (recommended)

```bash
git clone https://github.com/prtzb/sonos_anti_abuse.git
cd sonos_anti_abuse
docker-compose up -d
```

The first time you run `docker-compose up`, the image will be built for you before starting the container. 

The `docker-compose.yml` file runs the `monitor` subcommand without any switches per default. Edit the `command:` keyword in the file if you want to run it another way.

If you want to add a skiplist file of your own, make sure it's [properly formatted](https://github.com/prtzb/sonos_anti_abuse/blob/main/README.md#skipfiles) and simply place it in the `annoying` subdir. By default, `docker-compose.yml` will mount the ./annoying directory found in the root of this repo.

### Instructions Docker

First, prepare your skipfiles and put them it in the `./annoying` sub-directory (or anywhere really, just remember to edit the docker run command below).


Build the image:


    docker build -t sonos_anti_abuse .


Start the container:

```bash
docker run \
    -dit \
    --name sonos_anti_abuse \
    --network=host \
    --restart=always \ 
    -v ./annoying:/home/sonosantiabuse/annoying \
    sonos_anti_abuse monitor
```


### Logs

To see what songs have been skipped, you can check the logs like this:

```bash
docker logs sonos_anti_abuse
```

To watch the log in real time, run this:

```bash
docker attach sonos_anti_abuse
```
