#!/usr/bin/python
from __future__ import print_function
from subprocess import Popen, PIPE
import json
import logging
import pdb
import shlex
import sys

# define logging details
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %I:%M:%S %p')
formatter_no_source = logging.Formatter('%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %I:%M:%S %p')
ch = logging.StreamHandler() # console handler
ch.setLevel(logging.INFO)
ch.setFormatter(formatter_no_source)
fl = logging.FileHandler(sys.argv[2]) #file handler
fl.setLevel(logging.INFO)
fl.setFormatter(formatter)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(ch)
log.addHandler(fl)

def run_cmd(cmd, returnstring):
    log.debug('cmd is: {0}'.format(cmd))
    log.debug('returnstring is: {0}'.format(returnstring))
    cmdplus = shlex.split(cmd)
    try:
        process = Popen(cmdplus, stdout=PIPE)
        cmdoutput = process.communicate()
    except OSError as err:
        log.error('OS Exception occurred: {}'.format(err))
        return 0
    exitcode = process.wait()
    log.debug('cmd output is: {0}'.format(cmdoutput))
    log.debug('exitcode is: {0}'.format(exitcode))
    #pdb.set_trace()
    if returnstring in cmdoutput[0]:
        return 1
    else:
        return 0

def main():
    #pdb.set_trace()
    with open(sys.argv[1]) as f:
        config_json = json.load(f)


    check_command_syntax = config_json['check_command_syntax']
    check_command_result = config_json['check_command_result']
    remediation_command_syntax = config_json['remediation_command_syntax']
    remediation_command_result = config_json['remediation_command_result']

    if run_cmd(check_command_syntax, check_command_result):
        log.info('check command success')
    else:
        log.warn('check command failed. Running remediation command.')
        if run_cmd(remediation_command_syntax, remediation_command_result):
            log.info('remediation command success')
        else:
            log.error('error running remediation command')

if __name__ == "__main__":
    main()
