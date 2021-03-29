#!/usr/bin/env python3
# coding: utf-8

import json
import requests
from time import localtime

from aliyunsdkcore.client import AcsClient
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
from aliyunsdkalidns.request.v20150109.DescribeSubDomainRecordsRequest import DescribeSubDomainRecordsRequest

def print_log(text: str) -> None:
    print(f'[{"%.2d-%.2d-%.2d %.2d:%.2d:%.2d" % localtime()[:6]}]: {text}')

def get_proper_records(device_name: str = 'eth0') -> list:

    proper_records: list = []
    with open('/proc/net/if_inet6', 'r') as inet6_file:
        inet6_text: str = inet6_file.read()

    for inet6_row in inet6_text.splitlines():
        inet6_record: list = inet6_row.split()
        # ignore other device
        if inet6_record[5] != device_name:
            continue

        # ignore local address
        if inet6_record[0][:4] == 'fe80':
            continue

        # ignore secondary/deprecated/tentative/permanent addresses
        if (int(inet6_record[4], 16) & 135) != 0:
            continue

        proper_records.append(inet6_record[0])
    
    return proper_records

def cut_ipv6_str(ipv6_str: str) -> list:

    # remove leading zeros
    ipv6_units: list = [ipv6_str[i : i + 4].lstrip('0') for i in range(0, len(ipv6_str), 4)]

    # replace empty unit with '0'
    ipv6_units: list = [(i if i else '0') for i in ipv6_units]

    return ipv6_units

def select_pleasing_ipv6_address(ipv6_addresses: list) -> list:
    return sorted(ipv6_addresses, key=lambda x:x.count('0'))[0]

def format_ipv6(ipv6_address: list) -> str:
    return ':'.join(ipv6_address)

def send_server_chan(key: str, text: str, description: str) -> bool:
    message_data = {
        'text': text,
        'desp': description
    }
    print_log('(ServerChan) -> Send serverchan message...')
    send_response = requests.post(
        url=f'https://sc.ftqq.com/{key}.send',
        data=message_data
    )
    send_response.raise_for_status()
    
    if 'success' in send_response.text:
        print_log('Success!')
        return True
    print_log(f'(ServerChan) -> failed: {sendResponse.text}')
    return False

def update_record(alisdk_client: AcsClient, record_id: str, resource_record: str, record_type: str, record_value: str) -> dict:
    update_record_request = UpdateDomainRecordRequest()
    update_record_request.set_accept_format('json')
    update_record_request.set_RecordId(record_id)
    update_record_request.set_RR(resource_record)
    update_record_request.set_Type(record_type)
    update_record_request.set_Value(record_value)

    update_record_response = alisdk_client.do_action_with_exception(update_record_request)
    update_record_response_json = json.loads(update_record_response)
    return update_record_response_json

def get_current_dns_record(alisdk_client: AcsClient, subdomain: str) -> str:
    subdomain_records_request = DescribeSubDomainRecordsRequest()
    subdomain_records_request.set_accept_format('json')
    subdomain_records_request.set_SubDomain('ipv6.rayalto.top')

    subdomain_records_response = alisdk_client.do_action_with_exception(subdomain_records_request)
    subdomain_records_response_json = json.loads(subdomain_records_response)

    return subdomain_records_response_json['DomainRecords']['Record'][0]['Value']

try:
    with open('config.json', 'r') as config_file:
        user_config = json.load(config_file)
    ali_client = AcsClient(ak=user_config['AccessKeyId'], secret=user_config['AccessKeySecret'])
    current_record = get_current_dns_record(ali_client, f'{user_config["RR"]}.{user_config["DomainName"]}')
    current_ipv6_addresses = [cut_ipv6_str(i) for i in get_proper_records()]
    if current_record not in [format_ipv6(i) for i in current_ipv6_addresses]:
        print_log('(Main) -> Ipv6 address changed, update dns record...')
        new_ipv6_address = format_ipv6(select_pleasing_ipv6_address(current_ipv6_addresses))
        update_record(ali_client, user_config['RecordId'], user_config['RR'], user_config['RecordType'], new_ipv6_address)
        print_log('(Main) -> Success')
        send_server_chan(user_config['ServerChanKey'], f'树莓派IPv6更新成功', f'树莓派的IPV6地址更新为: {new_ipv6_address}')
    else:
        print_log('(main) -> No change, exit...')
except Exception as e:
    print_log('Failed: {e}')
    send_server_chan(user_config['ServerChanKey'], '树莓派IPv6更新失败', f'更新IPV6时出现错误: {e}')
