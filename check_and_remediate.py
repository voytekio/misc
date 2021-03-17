#!/usr/bin/python
from __future__ import print_function
#from subprocess import Popen, PIPE
from subprocess import check_output, CalledProcessError, STDOUT
from datetime import datetime
import json
import logging
import pdb
import os
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
level = logging.INFO
level = logging.DEBUG

if os.environ.get('SSH_TTY') or 'xterm' in os.environ.get('TERM'):
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


def run_cmd(cmd, return_output=False):
    logging.debug('cmd is: {0}'.format(cmd))
    #logging.debug('returnstring is: {0}'.format(returnstring))
    cmdplus = shlex.split(cmd)
    try:
        if ';' in cmd or '|' in cmd:
            ret = check_output(cmd, universal_newlines=True, stderr=STDOUT, shell=True).strip()
        else:
            ret = check_output(cmdplus, universal_newlines=True, stderr=STDOUT).strip()
        #process = Popen(cmdplus, stdout=PIPE)
        #cmdoutput = process.communicate()
    except CalledProcessError as err:
        logging.debug(f'"{cmd}" FAILED')
        ret_code = err.returncode
        return ((err.returncode, err.stdout) if hasattr(err, 'stdout') else (err.returncode, "cmd had no output"))
    except FileNotFoundError as err:
        return ((2, err.strerror) if hasattr(err, 'strerror') else (1, 'no sterror provided'))
    except OSError as err:
        #logging.error('OS Exception occurred: {}'.format(err))
        return (2, 'OSError occurred')
    logging.debug(f'cmd output is: {ret}')
    return (0, ret) if return_output else (0, '')
    '''
    exitcode = process.wait()
    # logging.debug('exitcode is: {0}'.format(exitcode))
    #pdb.set_trace()
    '''

def record_timestamp(event_source, event_id, event_timestamp, read_or_write):
    filename = './.eventindex_{}_{}.index'.format(event_source, event_id)
    try:
        #pdb.set_trace()
        with open(filename, read_or_write) as f:
            if read_or_write == 'w':
                f.write(str(event_timestamp))
            else:
                for one_line in f:
                    return one_line
    except FileNotFoundError:
        logging.warning('index file not found, ignoring')
        return None
    except:
        logging.error('Unable to write to file {}. Exiting'.format(filename))
        raise BaseException


def get_events(log_type, desired_event_id, desired_event_string=None, num_events_to_read=10):
    logging.debug('hello from get_events func. Args are: {}, {}, {}, {}'.format(log_type, desired_event_id, desired_event_string, num_events_to_read))
    import win32evtlog
    import winerror
    import win32evtlogutil
    log_handle = win32evtlog.OpenEventLog('localhost', log_type)
    total = win32evtlog.GetNumberOfEventLogRecords(log_handle)
    logging.debug('total # of events: {}'.format(total))
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

    i = 1
    #pdb.set_trace()
    last_timestamp_string = record_timestamp(log_type, desired_event_id, '', 'r')
    last_timestamp = datetime.strptime(last_timestamp_string, '%Y-%m-%d %H:%M:%S') if last_timestamp_string else None
    while True:
        all_events = win32evtlog.ReadEventLog(log_handle, flags, 0)
        if not all_events:
            win32evtlog.CloseEventLog(log_handle)
            return (0, '')
        logging.debug('Next batch, size: {}'.format(len(all_events)))
        for one_event in all_events:
            event_id = str(winerror.HRESULT_CODE(one_event.EventID))
            event_id = winerror.HRESULT_CODE(one_event.EventID)
            event_source = one_event.SourceName
            event_msg = win32evtlogutil.SafeFormatMessage(one_event, log_type)
            event_timestamp = one_event.TimeGenerated
            logging.debug('|{}| Event:\nID: {}, Timestamp: {}, Source: {}\nMessage: {}'.format(i, event_id, event_timestamp.Format(), event_source, event_msg))
            if i == 1:
                # remember the 1st event so that we dont have to scan all events next time
                record_timestamp(log_type, desired_event_id, event_timestamp, 'w')
            if last_timestamp and event_timestamp <= last_timestamp:
                logging.debug('already processed this event, will exit at this time.')
                win32evtlog.CloseEventLog(log_handle)
                return (0, '')
            if event_id == desired_event_id:
                logging.warning('Event matched, will return 1')
                logging.info('Event:\nID: {}, Timestamp: {}, Source: {}\nMessage: {}'.format(event_id, event_timestamp.Format(), event_source, event_msg))
                win32evtlog.CloseEventLog(log_handle)
                return (1, '')
            i = i + 1
            if i > int(num_events_to_read):
                win32evtlog.CloseEventLog(log_handle)
                return (0, '')

def main():
    args = parseargs()
    logging.info('Script start')

    with open(args.configfile) as f:
        config_json = json.load(f)

    remediation_command_syntax = config_json['remediation_command_syntax']
    remediation_command_result = config_json['remediation_command_result']
    debug_cmd_list_before = config_json.get('debug_cmd_list_before', [])
    debug_cmd_list_after = config_json.get('debug_cmd_list_after', [])
    if 'events' in args.mode:
        eventlog_type = config_json['eventlog_type']
        eventlog_search_string = config_json['eventlog_search_string']
        eventlog_id = config_json['eventlog_id']
        eventlog_num_of_events_to_check = config_json['eventlog_num_of_events_to_check']
        res = get_events(eventlog_type, int(eventlog_id), eventlog_search_string, eventlog_num_of_events_to_check)
    else:
        check_command_syntax = config_json['check_command_syntax']
        #check_command_result = config_json['check_command_result']
        #pdb.set_trace()
        res = run_cmd(check_command_syntax, return_output=True)

    if not res[0]:
        logging.info('check command success')
    elif res[0] == 1:
        logging.warning(f'check failed. Details: {res[1]}')
        logging.info('running debug cmds BEFORE remediation')
        for debug_cmd in debug_cmd_list_before:
            debug_cmd_res = run_cmd(debug_cmd, return_output=True)
            logging.info(f'{debug_cmd}: {debug_cmd_res[1]}')
        logging.warning('Running remediation command.')
        res_remediation_cmd = run_cmd(remediation_command_syntax, return_output=True)
        if not res_remediation_cmd[0]:
            logging.info('remediation command success judging by return code')
        else:
            logging.error(f'error running remediation command: {res_remediation_cmd[1]}')
        logging.info('running debug cmds AFTER remediation')
        for debug_cmd in debug_cmd_list_after:
            debug_cmd_res = run_cmd(debug_cmd, return_output=True)
            logging.info(f'{debug_cmd}: {debug_cmd_res[1]}')
    else:
        logging.error(f'Non-1 error while running cmd, check syntax. Script will exit. Error: {res[1]}')

    logging.info('Script finish')

if __name__ == "__main__":
    main()
