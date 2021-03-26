from subprocess import check_output, CalledProcessError, STDOUT
import logging
import pdb
import os
import platform
import shlex
import sys
import time
import argparse

# define logging details
level = logging.INFO
#level = logging.DEBUG

# setup logging
if os.environ.get('SSH_TTY') or (os.environ.get('TERM') and 'xterm' in os.environ.get('TERM')):
    handlers = [
        logging.FileHandler(sys.argv[0] + '.log'),
        logging.StreamHandler(),
    ]
else:
    handlers = [logging.FileHandler(sys.argv[0] + '.log')]

logging.basicConfig(
    level=level,
    format='%(asctime)s [%(name)s][%(levelname)s] %(message)s',
    handlers=handlers,
)


def parseargs():
    parser = argparse.ArgumentParser()

    parser.add_argument("-t","--target", help="target to ping", required=True, action = 'store')
    parser.add_argument("-s","--sleep", help="sleep in seconds, between each ping, default is 1", action = 'store', default = 1)
    parser.add_argument("-p","--interval_ping", help="how long in seconds to wait for ping reply, default is 1", action = 'store', default = 1)
    parser.add_argument("-i","--interval_log", help="how many iterations before writing an 'ok' msg to logfile, default is 60", action = 'store', default = 60)

    args = parser.parse_args()
    return args


def run_cmd(cmd, return_output=False):
    logging.debug('cmd is: {0}'.format(cmd))
    cmdplus = shlex.split(cmd)
    try:
        if ';' in cmd or '|' in cmd:
            ret = check_output(cmd, universal_newlines=True, stderr=STDOUT, shell=True).strip()
        else:
            ret = check_output(cmdplus, universal_newlines=True, stderr=STDOUT).strip()
    except CalledProcessError as err:
        logging.debug(f'"{cmd}" FAILED')
        ret_code = err.returncode
        return ((err.returncode, err.stdout) if hasattr(err, 'stdout') else (err.returncode, "cmd had no output"))
    except FileNotFoundError as err:
        return ((2, err.strerror) if hasattr(err, 'strerror') else (1, 'no sterror provided'))
    except OSError as err:
        return (2, 'OSError occurred')
    logging.debug(f'cmd output is: {ret}')
    return (0, ret) if return_output else (0, '')


def main():
    args = parseargs()
    logging.info(f'START script {sys.argv[0]}')
    c = 1
    target = args.target
    sleep_interval = args.sleep
    ping_wait_interval = args.interval_ping
    verbose_msg_interval = args.interval_log

    if platform.system().lower()=='windows':
        cmdline = f'ping -n 1 -w {1000*ping_wait_interval} {target}'
    else:
        cmdline = f'ping -c 1 -W {ping_wait_interval} {target}'

    all_settings = {}
    for setting in args._get_kwargs():
        all_settings[setting[0]] = setting[1]
    logging.info(f'All configuration settings are: {all_settings}')
    logging.info(f'cmdline is: {cmdline}')

    #pdb.set_trace()
    while True:
        res = run_cmd(cmdline, return_output=True)

        if res[0] or 'Destination host unreachable' in res[1]:
            logging.warning(f'ping failure. Output: {res[1]}')
            c = 0
        elif c % int(verbose_msg_interval) == 0:
            logging.info(f'pings are looking ok')
            c = 0
        else:
            logging.debug(f'pings are looking ok')
        c += 1
        time.sleep(sleep_interval)
    logging.info('END script {sys.argv[0]}\n')


if __name__ == "__main__":
    main()
