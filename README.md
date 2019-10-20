# misc
miscellaneous stuff

## check_and_remediate
## example cmd:
    ./check_and_remediate.py -m events -c rras_event.json
## example json:
```
{
    "eventlog_type": "system",
    "eventlog_search_string": "pause",
    "eventlog_id": "27",
    "eventlog_num_of_events_to_check": "50",
    "remediation_command_syntax": "cmd /c 'net stop w32time && net start w32time'",
    "remediation_command_result": "service was started successfully"
}
```
