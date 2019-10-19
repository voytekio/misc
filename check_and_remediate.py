#!/usr/bin/python
from __future__ import print_function
from subprocess import Popen, PIPE
import json
import logging
import pdb
import shlex
import sys
import argparse

def parseargs():
    parser = argparse.ArgumentParser()

    parser.add_argument("-c","--configfile", help="name of config json", required=True, action = 'store')
    parser.add_argument("-l","--logfile", help="name of log file", action = 'store', default = 'check_and_act.log')
    #parser.add_argument("-e","--execute", help="use to make changes; otherwise read-only", action = 'store_true')
    parser.add_argument("-m","--mode", help="mode - either cmds or events", action = 'store', default = 'cmds.log')

    #action = 'store' is default (and can even be omitted)
    #action = 'store_true' or 'store_false' are for flags:
    #    if user specifes --execute, then args.execute will evaulate to True; otherwise False

    args = parser.parse_args()
    return args

# define logging details
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %I:%M:%S %p')
formatter_no_source = logging.Formatter('%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %I:%M:%S %p')
ch = logging.StreamHandler() # console handler
ch.setLevel(logging.INFO)
ch.setFormatter(formatter_no_source)
fl = logging.FileHandler(sys.argv[0] + '.log') #file handler
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
    if returnstring in str(cmdoutput[0]):
        return 1
    else:
        return 0

def get_events(log_type, desired_event_id, desired_event_string=None, num_events_to_read=10):
    print('hello from get_events func')
    print('args are: {}, {}, {}, {}'.format(log_type, desired_event_id, desired_event_string, num_events_to_read))
    import win32evtlog
    import winerror
    import win32evtlogutil
    log_handle = win32evtlog.OpenEventLog('localhost', log_type)
    total = win32evtlog.GetNumberOfEventLogRecords(log_handle)
    print('total # of events: {}'.format(total))
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

    i = 1
    while True:
        all_events = win32evtlog.ReadEventLog(log_handle, flags, 0)
        if not all_events:
            win32evtlog.CloseEventLog(log_handle)
            return 1
        print('Next batch, size: {}'.format(len(all_events)))
        for one_event in all_events:
            event_id = str(winerror.HRESULT_CODE(one_event.EventID))
            event_id = winerror.HRESULT_CODE(one_event.EventID)
            event_source = one_event.SourceName
            event_msg = win32evtlogutil.SafeFormatMessage(one_event, log_type)
            if event_id == desired_event_id:
                print('Event:\nID: {}, Source: {}\nMessage: {}'.format(event_id, event_source, event_msg))
                win32evtlog.CloseEventLog(log_handle)
                return 0
            else:
                #print('Event:\nID: {}, Source: {}\nMessage: {}'.format(event_id, event_source, event_msg))
                print('Nope: {}: {}'.format(i, event_id))
            i = i + 1
            if i > int(num_events_to_read):
                win32evtlog.CloseEventLog(log_handle)
                return 1

    win32evtlog.CloseEventLog(log_handle)
    return 1

def main():
    #pdb.set_trace()

    args = parseargs()

    #and finally get to your data:
    #- print "user is:",args.user    (uses the longer name)
    #- if args.execute:
    #        print "RW"
    #    else:
    #        print "RO"

    with open(args.configfile) as f:
        config_json = json.load(f)

    if 'events' in args.mode:
        eventlog_type = config_json['eventlog_type']
        eventlog_search_string = config_json['eventlog_search_string']
        eventlog_id = config_json['eventlog_id']
        eventlog_num_of_events_to_check = config_json['eventlog_num_of_events_to_check']
        res = get_events(eventlog_type, int(eventlog_id), eventlog_search_string, eventlog_num_of_events_to_check)
        print('res is: {}'.format(res))
    #sys.exit(1)

    else:
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
    #if cmd -> get_cmd, run_cmd, compare_output
    #if pyt -> importe mod, execute known func inside module(or passt that too), compare_output 
