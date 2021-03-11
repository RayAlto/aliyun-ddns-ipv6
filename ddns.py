#!/usr/bin/env python3
# coding: utf-8

import json
import requests
import netifaces

from aliyunsdkcore.client import AcsClient
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
from aliyunsdkalidns.request.v20150109.DescribeSubDomainRecordsRequest import DescribeSubDomainRecordsRequest

def get_ipv6_address() -> list:
    ipv6_addresses = []
    for interface in netifaces.interfaces():
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET6 not in addresses:
            # Not ipv6
            continue
        for address in netifaces.ifaddresses(interface)[netifaces.AF_INET6]:
            if(interface not in address['addr']):
                # Get address without interface name
                ipv6_addresses.append(address['addr'])

    # Remove local
    ipv6_addresses.remove('::1')

    return ipv6_addresses

def send_server_chan(key: str, text: str, description: str) -> bool:
    message_data = {
        'text': text,
        'desp': description
    }
    send_response = requests.post(
        url=f'https://sc.ftqq.com/{key}.send',
        data=message_data
    )
    send_response.raise_for_status()
    
    if 'success' in send_response.text:
        print('发送Server酱成功。')
        return True
    print(f'发送Server酱失败：{sendResponse.text}')
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
    subdomain_records_request.set_SubDomain(subdomain)

    subdomain_records_response = alisdk_client.do_action_with_exception(subdomain_records_request)
    subdomain_records_response_json = json.loads(subdomain_records_response)

    return subdomain_records_response_json['DomainRecords']['Record'][0]['Value']

try:
    with open('config.json', 'r') as config_file:
        user_config = json.load(config_file)
    print('登录阿里云')
    ali_client = AcsClient(ak=user_config['AccessKeyId'], secret=user_config['AccessKeySecret'])
    print('获取当前dns记录')
    current_record = get_current_dns_record(ali_client, f'{user_config["RR"]}.{user_config["DomainName"]}')
    print('获取本机ipv6地址')
    new_ipv6_address = get_ipv6_address()[0]

    if current_record != new_ipv6_address:
        print('地址发生了变化，尝试更新记录')
        update_record(ali_client, user_config['RecordId'], user_config['RR'], user_config['RecordType'], new_ipv6_address)
        print('更新成功')
        if user_config['ServerChanKey']:
            print('发送server酱')
            send_server_chan(user_config['ServerChanKey'], f'IPV6地址更新为: {new_ipv6_address}', f'更新成功')
except Exception as e:
    print('发生错误')
    send_server_chan(user_config['ServerChanKey'], '更新IPV6时出现错误: {e}', '更新失败')
