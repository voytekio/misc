#!/usr/bin/python
from __future__ import print_function
import logging
import os
import sys
import boto3

# import ipdb
import pdb
from subprocess import Popen, PIPE
import shlex

# v.0.4
# sample usage:
# cd .virtenvs/boto3/bin/; source activate; python <loc>/boto_s3.py <file_to_upload.txt>; deactivate

formatter = logging.Formatter(
    '%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y/%m/%d %I:%M:%S %p'
)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
fl = logging.FileHandler(sys.argv[0] + '.log')
fl.setLevel(logging.INFO)
fl.setFormatter(formatter)
log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(ch)
log.addHandler(fl)


def list_objects(s3_r, bucket):
    log.debug('inside list objects func')
    for one_object in bucket.objects.all():
        log.debug(one_object.key)


def list_buckets(s3_client, s3_r):
    log.debug('inside list bkts func')
    bucket_list = []
    for one_bucket in s3_r.buckets.all():
        log.debug(one_bucket.name)
        bucket_list.append(one_bucket)
    return bucket_list


def upload_file(s3_client, s3_r, filename, bucket, public=True):
    # ipdb.set_trace()
    log.debug('inside upload file func')
    s3_filename = filename.split('/')[-1]
    file_object = bucket.Object(s3_filename)
    if public:
        file_object.upload_file(filename, ExtraArgs={'ACL': 'public-read'})
    else:
        file_object.upload_file(filename)


def download_file(s3_r, s3_filename, path, bucket):
    # ipdb.set_trace()
    log.debug('inside download file func')
    file_object = bucket.Object(s3_filename)
    file_object.download_file(os.path.join(path, s3_filename))


def file_current(filename, marker_filename):
    # ipdb.set_trace()
    if not os.path.exists(marker_filename):
        log.info('no marker_filename; will upload the file')
        return False
    marker_timestamp = os.path.getmtime(marker_filename)
    file_timestamp = os.path.getmtime(filename)

    if file_timestamp > marker_timestamp:
        log.info('file changed')
        return False
    else:
        log.info('no modifications to file')
        return True


def internet_available(inet_ip):
    wait_time = 1000 if 'Darwin' in os.uname()[0] else 1
    cmd_to_run = '/sbin/ping -c 1 -W {} {}'.format(wait_time, inet_ip)
    ping_res = run_cmd(cmd_to_run)
    if ping_res[1] == 0:
        log.info('able to get to internet.')
        return True
    else:
        log.warn('unable to get to internet.')
        return False


def run_cmd(cmd_line, log_output=False):
    cmdplus = shlex.split(cmd_line)
    log.info('cmdplus is: {}'.format(cmdplus))
    process = Popen(cmdplus, stdout=PIPE)
    cmdoutput = process.communicate()
    exit_code = process.wait()
    if log_output:
        log.warn(cmdoutput[0])
    return (cmdoutput[0], exit_code)


def main():
    # pdb.set_trace()
    inet_ip = '4.2.2.1'
    log.info('=================== starting s3 script')

    filename = sys.argv[1]
    marker_filename = os.path.join(
        os.path.split(filename)[0], ('.{}_marker'.format(os.path.split(filename)[1]))
    )
    if file_current(filename, marker_filename):
        log.info('No need to re-upload, file up-to-date.')
        return True
    log.info('Will attempt to upload modified copy to s3')

    if not internet_available(inet_ip):
        log.warn('no internet connection, dont bother')
        return True
    log.info('able to reach s3. continuing with upload')

    s3_client = boto3.client('s3')
    s3_r = boto3.resource('s3')
    bucket_list = list_buckets(s3_client, s3_r)
    bucket = bucket_list[0] if bucket_list else None
    # list_objects(s3_r, bucket)

    try:
        upload_file(s3_client, s3_r, filename, bucket)
        # download_file(s3_r, 'tklr_0.txt', 'meh/meh2', bucket)
    except:
        log.warn('exception while running upload. will not continue.')
        return False

    # create markerfile:
    try:
        with open(marker_filename, 'w') as f:
            f.write('just_a_marker_file_used_for_date_comparisons\n')
    except:
        log.warn('exception while writing market_file')
        return False
    log.info('success')


if __name__ == "__main__":
    main()
