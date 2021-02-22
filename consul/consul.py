import base64
import requests
import pprint
import pdb
import sys

# example curl http://127.0.0.1:8500/v1/kv/servers?recurse=true
consul_host = '127.0.0.1'
consul_port = '8500'
http_prefix = f'http://{consul_host}:{consul_port}/v1/kv/'
query_strings = '?recurse=true' #&?raw=true

global_dict = {}

def _decode(value):
    val_bytes = base64.b64decode(value)
    val = val_bytes.decode('ascii')
    return val

def get(http_prefix, consul_prefix, query_strings='?recurse=true'):
    final_url = http_prefix + consul_prefix + query_strings
    print(final_url)
    resp = requests.get(final_url)
    # TODO: add error handling
    ret_list = []
    for record in resp.json():
        value = _decode(record['Value'])
        ret_list.append({'key': record['Key'], 'value': value})
    return ret_list

def parse_servers(global_dict, records):
    for record in records:
        key = record['key'].split('/')[2]
        value = record['value']
        attrib = record['key'].split('/')[3]
        if global_dict.get(key):
            global_dict[key][attrib] = value
        else:
            global_dict[key] = {}
            global_dict[key][attrib] = value

def main(): #generate alias list
    servers = get(http_prefix, 'v2/servers')
    pprint.pprint(servers)
    parse_servers(global_dict, servers)
    print(global_dict)
    s1 = ''
    user = sys.argv[1]
    for server_name, server_attribs in global_dict.items():
        temp_s = f'alias {server_name} {user}@{server_attribs["fqdn"]}\n'
        s1+=temp_s
    print(s1)

if __name__ == '__main__':
    main()
