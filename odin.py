import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

# Convenience print funcs
def nice(s=''): print(f'  ✔ {s}')
def damn(s=''): print(f'  ✖ {s}')


#
# Help screen
#
def help():

    print('\n'
          'Usage: python odin.py <COMMAND> <WORLDNAME> [..OPTIONS]\n\n'

          '    Manage valheim server instances\n'
          '      (Password is always 123456)\n\n'

          '<COMMAND>\n'
          ' create <world>            Creates a new server\n'
          ' start  <world> [-p PORT]  Starts a server (default port: 2456)\n'
          ' backup <world>            Backup a world\n'
          ' update <world>            Update server files\n'
          ' help                      You\'re looking at it\n')


#
# Get relative dir
#
def odin_path(*path_names):

    root = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(root, *path_names)
    return os.path.abspath(path)


#
# Download steamcmd and create necessary dirs
#
def setup():

    # Paths
    dl_url       = 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip'
    dl_path      = odin_path('steamcmd.zip')
    steamcmd_dir = odin_path('steamcmd')
    steamcmd_exe = odin_path('steamcmd', 'steamcmd.exe')
    worlds_dir   = odin_path('worlds')
    
    # Silently make worlds dir
    if not os.path.exists(worlds_dir):
        os.mkdir(worlds_dir)
        nice(f'Created directory: {worlds_dir}')

    # Exit if steamcmd dir already exists
    if os.path.exists(steamcmd_dir):
        damn(f'Directory already exists: {steamcmd_dir}')
        exit(1)

    # Prep steamcmd dir
    os.mkdir(steamcmd_dir)
    nice(f'Created directory: {steamcmd_dir}')

    # Download steamcmd.zip and extract
    with urllib.request.urlopen(dl_url) as dl:
        with open(dl_path, 'wb') as z:
            z.write(dl.read())
            nice('Downloaded steamcmd')

        with zipfile.ZipFile(dl_path, 'r') as z:
            z.extractall(steamcmd_dir)
            nice(f'Extracted steamcmd to {steamcmd_dir}')

    # Delete zip after extraction
    os.remove(dl_path)
    nice(f'Removed {dl_path}')


#
# Sanitary checks before running Odin
#
def prerun(args):

    arg_len    = len(args)
    valid_cmds = ('create', 'start', 'backup', 'update', 'help')

    servers_dir  = odin_path('servers')
    worlds_dir   = odin_path('worlds')
    steamcmd_dir = odin_path('steamcmd')

    if not os.path.exists(steamcmd_dir):
        nice("No steamcmd detected. Running first-time setup..")
        setup()

    if not os.path.exists(worlds_dir):
        os.mkdir(worlds_dir)
        nice(f'Created directory: {worlds_dir}')

    if not os.path.exists(servers_dir):
        os.mkdir(servers_dir)
        nice(f'Created directory: {servers_dir}')

    # No args provided
    if arg_len == 0:
        help()
        exit(0)

    # Help command
    elif args[0] == 'help':
        help()
        exit(0)

    # Err: exit on invalid command
    elif not args[0] in valid_cmds:
        print(f'{args[0]} is an invalid command')
        help()
    
    # Err: insufficient args
    elif arg_len < 2:
        print(f'Expecting at least 2 args but only received {arg_len}.')
        help()

    # Args are valid
    else:
        return True

    # Args are invalid
    return False


#
# Downloads valheim server files 
# and creates a new server
#
def create(name, update=False):

    server_dir   = odin_path('servers', name)
    steamcmd_bin = odin_path('steamcmd', 'steamcmd.exe')

    if update and not os.path.exists(server_dir):
        damn(f"Can't update server because it doesn't exist: {server_dir}")
        exit(1)

    if not update:
        if os.path.exists(server_dir):
            damn(f'Directory already exists: {server_dir}')
            exit(1)
        else:
            os.mkdir(server_dir)
            nice(f'Created directory: {server_dir}')

    # Download server files through steamcmd
    cmd = [
        steamcmd_bin, '+login', 'anonymous', 
        '+force_install_dir', server_dir, 
        '+app_update', '896660', 
        'validate', '+exit'
    ]

    exit_code = subprocess.check_call(cmd,
                        stdout=sys.stdout,
                        stderr=subprocess.STDOUT)

    if exit_code != 0:
        damn(f'A problem occurred while downloading server files. Reverting..')

        # Delete the failed server directory
        try:
            shutil.rmtree(server_dir)
        except OSError as e:
            print (f"Error: {e.filename} - {e.strerror}.")
            exit(1)

    nice(f'Server files downloaded')


#
# Starts a server
#
def start(args):

    args_len   = len(args)
    server_dir = odin_path('servers', args[0])
    server_bin = odin_path('servers', args[0], 'valheim_server.exe')
    world_dir  = odin_path('worlds', args[0])
    start_args = {}

    if not os.path.exists(server_dir):
        damn(f"Server doesn't exist: {server_dir}")
        exit(1)

    # Too lazy to use argparse
    start_args['name'] = args[0]
    args_str = ' '.join(args)

    # Extract port arg
    port = re.match(args_str, r'(?:-p|--port)\s(\d+)')

    # Use port provided, otherwise default to 2456
    start_args['port'] = port[0] if port != None else '2456'

    spawn_cmd = ( 'cmd /C '
                  'set SteamAppId=892970 && '
                  f'{server_bin} -nographics -batchmode '
                  f'-name {start_args["name"]} -world {start_args["name"]} '
                  f'-port {start_args["port"]} '
                  f'-password 123456 ' 
                  f'-savedir {server_dir}')

    print('Tip: Press CTRL+C to save and quit server')
    time.sleep(1)

    p = subprocess.Popen(spawn_cmd, start_new_session=True)


def main():
    args = sys.argv[1:]

    if not prerun(args): 
        exit(1)

    cmd  = args[0]
    name = args[1]

    if   cmd == 'create' : create(name)
    elif cmd == 'update' : create(name, update=True)
    elif cmd == 'start'  : start(args[1:])
    elif cmd == 'backup' : print("Not implemented lol.")


if __name__ == "__main__": main()