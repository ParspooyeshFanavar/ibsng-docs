#!/usr/bin/env python

import requests
import json
import os

url = 'http://127.0.0.1:1237'

auth_type = os.environ.get('IBS_AUTH_TYPE', 'ADMIN')
if auth_type not in ('ADMIN', 'NORMAL_USER', 'VOIP_USER'):
    raise ValueError('invalid IBS_AUTH_TYPE=%r' % (auth_type,))
auth_name = os.environ.get('IBS_AUTH_NAME', 'system')
auth_pass = os.environ.get('IBS_AUTH_PASS')
if not auth_pass:
    raise ValueError(
        "You need to set environment variable IBS_AUTH_PASS"
        ", and possbly IBS_AUTH_TYPE and IBS_AUTH_NAME."
    )

auth_remoteaddr = os.environ.get("IBS_ADDR", "127.0.0.1")
auth_session = os.environ.get('IBS_AUTH_SESSION')


#################################################

def baseCall(method, **params):
    response = requests.post(
        url,
        data=json.dumps({
            'method': method,
            'params': params,
            #'jsonrpc': '2.0',
            #'id': 0,
        }),
        headers={
            'content-type': 'application/json'
        },
    ).json()

    error = response.get('error')
    if error:
        raise Exception(error)
    return response['result']

def call(method, **params):
    if auth_session:
        print('Using auth_session=%r' % (auth_session,))
        params['auth_session'] = auth_session
    else:
        params.update({
            'auth_type': auth_type,
            'auth_name': auth_name,
            'auth_pass': auth_pass,
            'auth_remoteaddr': auth_remoteaddr,
            'date_type': 'gregorian',
        })
    return baseCall(method, **params)



def callSaveJson(fpath, method, **params):
    data = call(method, **params)
    text = json.dumps(
        data,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    ).encode('utf-8')
    open(fpath, 'w').write(text)
    return data

def testUssdPayment():
    call(
        'online_payment.ussdPaymentVerifiedForUser',
        user_id = 107455,
        amount = 1234,
        comment = 'saeed'
    )

#################################################

def getOnlineUsers():
    internet_onlines, voip_onlines = callSaveJson(
        '/tmp/onlines.json',
        'report.getOnlineUsers',
        normal_sort_by='user_id',
        normal_desc=False,
        voip_sort_by='user_id',
        voip_desc=False,
        conds={},
    )
    print('%4d Internet Onlines' % len(internet_onlines))
    print('%4d VoIP Onlines' % len(voip_onlines))

def updateUsernamePassword(user_id, username, password):
    call(
        'user.updateUserAttrs',
        user_id=str(user_id),
        attrs={
            'normal_user_spec': {
                'normal_username': username,
                'normal_password': password,
            }
        },
        to_del_attrs=[],
    )

def getLockedUsers():
    params = {
        'conds': {
            'lock': '',
        },
        'from': 0,
        'to': 10,
        'order_by': 'user_id',
        'desc': False,
    }
    result = call(
        'user.searchUser',
        **params
    )
    total_count = result[0]
    total_credit = result[1]
    user_ids = result[2]
    print("total_credit:", total_credit)
    print("total_count:", total_count, "==", len(user_ids))
    print("user_ids:", user_ids)

def getUsernameByFailedUserIP(ip):
    return call(
        'util.getUsernameByFailedUserIP',
        ip=ip,
    )

def test_getInOutUsages():
    params = {
        'conds': {
            'logout_time_from': '2',
            'logout_time_from_unit': 'minutes',
        },
        'from': 0,
        'to': 5,
        'order_by': 'sum',
    }
    pprint(call(
        'report.getInOutUsages',
        **params
    ))


def test_prefix_usage():
    params = {
        'conds': {
            'logout_time_from': '1',
            'logout_time_from_unit': 'minutes',
            'group_by': 'prefix_name',
        },
        'from': 0,
        'to': 5,
        'order_by': 'count',
        'desc': True,
    }
    pprint(call(
        'report.getPrefixNameUsage',
        **params
    ))


def test_credit_changes():
    params = {
        'conds': {
            "user_view": "",
            #'action': [
            #    'ADD_USER',
            #    'CHANGE_CREDIT',
            #    'RENEW',
            #],
            #'change_time_from': '5',
            #'change_time_from_unit': 'hours',
        },
        'from': 0,
        'to': 10,
        'sort_by': 'change_time',
        'desc': True,
    }
    pprint(call(
        'report.getCreditChanges',
        **params
    ))


def test_save_credit_changes():
    params = {
        'conds': {
            'action': [
                'ADD_USER',
                'CHANGE_CREDIT',
                'RENEW',
            ],
            'change_time_from': '5',
            'change_time_from_unit': 'hours',
        },
        'cols': [
            'change_time_formatted',
            'admin_name',
            'change_time',
            'credit_change_id',
            'action',
            'action_text',
            'admin_id',
            'comment',
            'per_user_credit',
            'remote_addr',
            'isp_credit',
            'isp_id',
            'user_ids',
            'isp_name',
            'name',
            'serial',
            'user_id',
            'username',
            'before_credit',
            'group',
            'group_id',
        ],
        'sort_by': 'change_time',
        'desc': True,
        'output_type': 'csv',
    }
    pprint(call(
        'report.saveCreditChanges',
        **params
    ))

def test_user_deposit_changes():
    params = {
        'conds': {
            #'deposit': 1000,
            #'deposit_op': '<',
            #'action': [
            #    'RENEW',
            #],
            'change_time_from': '5',
            'change_time_from_unit': 'hours',
            'isp_names': [
                'Dejkhah',
                'Hemat',
                'KH',
            ],
        },
        'from': 0,
        'to': 10,
        'sort_by': 'change_time',
        'desc': True,
    }
    pprint(call(
        'report.getUserDepositChanges',
        **params
    ))


def test_user_audit_logs():
    params = {
        'conds': {
        },
        'from': 0,
        'to': 10,
        'sort_by': 'change_time',
        'desc': True,
    }
    pprint(call(
        'report.getUserAuditLogs',
        **params
    ))

def test_isp_deposit_changes():
    params = {
        'conds': {
            'change_time_from': '5',
            'change_time_from_unit': 'hours',
            'isp_names': [
                'Dejkhah',
                'Hemat',
                'KH',
            ],
        },
        'from': 0,
        'to': 10,
        'sort_by': 'isp_deposit_change_time',
        'desc': True,
    }
    pprint(call(
        'report.getISPDepositChangeLogs',
        **params
    ))

def test_temp_extend_users():
    params = {
        'conds': {
            #'temporary_extend_date_from': '10',
            #'temporary_extend_date_from_unit': 'days',
        },
        'from': 0,
        'to': 10,
        'sort_by': 'temporary_extend_date',
        'desc': True,
    }
    pprint(call(
        'report.getTemporaryExtendLogs',
        **params
    ))

def test_management_summary():
    params = {
        'conds': {
            'view_period': 'daily',
            'included_objects': [
                'isp',
                'isp_mapped_user',
                'group',
                'ras',
                'ras_group',
                'ras_isp',
                'service',
            ],
            'report_targets': [
                'duration',
                'credit',
                'in_bytes',
                'out_bytes',
            ],
            'login_time_from': '5',
            'login_time_from_unit': 'minutes',
        },
        'from': 0,
        'to': 10,
        'sort_by': '',
        'desc': True,
    }
    pprint(call(
        'report.getManagementSummaryReport',
        **params
    ))



def test_system_audit_logs():
    params = {
        'conds': {
            'change_time_from': '5',
            'change_time_from_unit': 'hours',
        },
        'from': 0,
        'to': 10,
        'sort_by': 'change_time',
        'desc': True,
    }
    pprint(call(
        'report.getSystemAuditLogs',
        **params
    ))


def test_online_payment_report():
    params = {
        'conds': {
            #'payment_date_from': '5',
            #'payment_date_from_unit': 'hours',
        },
        'from': 0,
        'to': 10,
        'sort_by': 'payment_date',
        'desc': True,
    }
    pprint(call(
        'report.getOnlinePaymentReport',
        **params
    ))

def test_save_connection_usage():
    params = {
        'report_type': 'inout_usages',
        'conds': {
            'login_time_from': '5',
            'login_time_from_unit': 'minutes',
        },
        'cols': [
            'creation_date',
            'user_id',
            'name',
            'user_name',
            'isp_name',
            'group_name',
            'serial',
        ],
        'sort_by': 'sum',
        'output_type': 'csv',
    }
    pprint(call(
        'report.saveConnectionUsages',
        **params
    ))

def getNotifications():
    params = {
    }
    pprint(call(
        'SystemNotification.getNotifications',
        **params
    ))

def changeNotificationStatus():
    pprint(call(
        'SystemNotification.changeNotificationStatus',
        notification_id=4,
        read=True,
    ))

def removeNotifications():
    pprint(call(
        'SystemNotification.removeNotifications',
        notification_ids=[
            9,
        ],
    ))

def getRemainingByteDuration():
    pprint(call(
        'telephony_support.getRemainingByteDuration',
        user_id=786,
    ))


def test_adminSearchSentMessage():
    params = {
        'conds': {
            'msg_types': [
                'SMS',
            ],
        },
        'from': 0,
        'to': 10,
        'order_by': 'message_id',
        'desc': True,
    }
    pprint(call(
        'mc.adminSearchSentMessage',
        **params
    ))

def test_updateUserAttrs(user_id):
    # from time import strptime, mktime
    ## real_first_login: no change, no delete
    ## delete assign_dns_1, deletes both
    ## update assign_dns_1, requires assign_dns_2
    call(
        'user.updateUserAttrs',
        user_id=str(user_id),
        attrs={
            'limit_usage_days': 5,
            #'save_bw_usage': '',# true_if_exists
            #'allow_user_disconnect': '',# true_if_exists
            #'deny_change_password': '',# true_if_exists
            #'auto_renew': '',# true_if_exists
            #'reset_negative_credit_on_renew': '',# true_if_exists
            ##'renew_do_not_reset_credit': '',# true_if_exists
            #'renew_do_not_reset_credit_on_state_package': '',# true_if_exists
            #'renew_do_not_reset_credit_on_state_recharged': '',# true_if_exists
            #'auto_renew_on_credit_finish': '',# true_if_exists
            #'auto_renew_do_not_reset_credit': '',# true_if_exists
            #'auto_recharge': '',# true_if_exists
            #'allow_recharge_by_voucher': '',# true_if_exists
            #'prevent_web_login': '',# true_if_exists
            #'enable_failed_login': '',# true_if_exists
            #'ignore_idle_threshold_static_ip': '',# true_if_exists
            #'ignore_idle_threshold': '',# true_if_exists
            #'caller_id_bind_on_login': '',# true_if_exists
            #'limit_mac_bind_on_login': '',# true_if_exists
            #'limit_port_bind_on_login': '',# true_if_exists
            #'limit_ras_bind_on_login': '',# true_if_exists
            #'limit_station_ip_bind_on_login': '',# true_if_exists
            ##'is_deposit_transferee': '',# true_if_exists
            ##'is_deposit_transferer': '',# true_if_exists
            #'normal_user_spec': {
            #    'normal_username': 'pptest',
            #    'normal_password': 'pptest',
            #}
            #'voip_user_spec': {
            #    'voip_username': 'pptest',
            #    'voip_password': 'pptest',
            #},
            #'first_login': int(mktime(strptime('2012-01-01 13:23', '%Y-%m-%d %H:%M'))),
            #'charge': 'charge2',
            #'abs_exp_date': '2017-01-01 13:23',
            #'abs_exp_date_unit': 'gregorian',
            #'abs_exp_date': '2',
            #'abs_exp_date_unit': 'years',
            #'assign_dns_1': '1.1.1.1',
            #'assign_dns_2': '1.1.1.2',
            #'assign_ip': '1.2.3.4',
            #'assign_netmask': '255.255.255.1',
            #'assign_route_ip': '1.2.3.4',
            #'caller_id': '12345',
            #'fast_dial': ['1' for i in range(20)],
            #'forward_number': '12345',
            #'asterisk_extension': 'test5',
            #'asterisk_ras_ip': '1.2.3.4',
            #'asterisk_sip_details': {
            #    'allow': 'none',
            #    'canreinvite': 'no',
            #},
            #'asterisk_iax_details': {},
            #'negative_credit_start': '',
        },
        to_del_attrs=[
            ## true_if_exists
            #'auto_renew',
            #'auto_recharge',
            #'auto_renew_on_credit_finish',
            #'auto_renew_do_not_reset_credit',
            #'reset_negative_credit_on_renew',
            #'allow_recharge_by_voucher',
            #'allow_user_disconnect',            
            #'caller_id_bind_on_login',
            #'deny_change_password',
            #'enable_failed_login',
            #'is_deposit_transferee',
            #'is_deposit_transferer',
            #'limit_mac_bind_on_login',
            #'limit_port_bind_on_login',
            #'limit_ras_bind_on_login',
            #'limit_station_ip_bind_on_login',
            #'prevent_web_login',
            #'negative_credit_start',
            #'save_bw_usage',
            #'ignore_idle_threshold',

            #'forward_number',
            #'fast_dial',
            #'assign_route_ip',
            #'assign_netmask',
            #'assign_ip',
            #'assign_dns_1',
            #'abs_exp_date_unit',
            #'abs_exp_date',
            #'charge',
            #'first_login',
        ],
    )


def test_saveSearchExpiredUsers():
    from time import sleep
    params = {
        'output_type': 'csv',
        'conds': {
            'group_name': 'pptest',
        },
        'order_by': 'user_id',
        'desc': False,
        'basic': 'user_id',
        'attrs': ','.join([
            'save_bw_usage',# true_if_exists
            'normal_username',
            'allow_user_disconnect',# true_if_exists
            'charge',
            'deny_change_password',# true_if_exists
            'auto_renew',# true_if_exists
            'reset_negative_credit_on_renew',# true_if_exists
            ##'renew_do_not_reset_credit',# true_if_exists
            'renew_do_not_reset_credit_on_state_package',# true_if_exists
            'renew_do_not_reset_credit_on_state_recharged',# true_if_exists
            'auto_renew_on_credit_finish',# true_if_exists
            'auto_renew_do_not_reset_credit',# true_if_exists
            'auto_recharge',# true_if_exists
            'allow_recharge_by_voucher',# true_if_exists
            'prevent_web_login',# true_if_exists
            'enable_failed_login',# true_if_exists
            'ignore_idle_threshold_static_ip',# true_if_exists
            'ignore_idle_threshold',# true_if_exists
            'caller_id_bind_on_login',# true_if_exists
            'limit_mac_bind_on_login',# true_if_exists
            'limit_port_bind_on_login',# true_if_exists
            'limit_ras_bind_on_login',# true_if_exists
            'limit_station_ip_bind_on_login',# true_if_exists
            ##'is_deposit_transferee',# true_if_exists
            ##'is_deposit_transferer',# true_if_exists
        ])
    }

    call(
        'user.saveSearchExpiredUsers',
        **params
    )
    sleep(2)
    printSystemNotifications()

def printSystemNotifications():
    import HTMLParser
    notifications = call(
        'SystemNotification.getNotifications',
        last_notifications=100,
        only_unread=True,
    )
    notifications.sort(
        key = lambda row: -row['notification_id']
    )
    for row in notifications:
        print('ID: %s'%row['notification_id'])
        print('Date: %s'%row['date'])
        print('Type: %s'%row['type'])
        link = row['links']
        if link:
            if '://' not in link:
                if not link.startswith('/'):
                    link = '/' + link
                link = 'http://127.0.0.1' + link
            print('Link: %s'%link)
        print('Message:\n%s'%HTMLParser.HTMLParser().unescape(row['message']))
        print('_______________________________________________________\n')


def test_searchUser():
    params = {
        'conds': {
            #'charge': 'charge2',
            #'group_name': [
            #    'pptest',
            #    '30-days-from-renew',
            #],
            #'ippool': ['test'],
            #'isp_names': 'test-isp',
            #'isp_id': '3',
            #'limit_usage_days': [5, 6, 7],
            #'mikrotik_address_list': ['Mik', 'aaaaaaaaa'],
            #'mikrotik_address_list_op': 'like',
            #'notification_profile': ['test'],
            'user_status': [1],
        },
        'from': 0,
        'to': 10,
        'order_by': 'user_id',
        'desc': False,
    }
    count, total_credit, user_ids = call(
        'user.searchUser',
        **params
    )
    print('Found %s users' % count)
    print('User IDs: %s' % user_ids)


def test_searchAdminLoginHistory():
    return call(
        'login.searchAdminLoginHistory',
        conds={
            'admin': 'parspooyesh',
        },
        _from=0,
        to=2,
        sort_by='login_time',
        desc=True,
    )

def test_webLogin():
    from pprint import pprint
    pprint(baseCall(
        'login.webLogin',
        auth_type="ANONYMOUS",
        auth_name="",
        auth_pass="",
        login_auth_type=auth_type,
        login_auth_name=auth_name,
        login_auth_pass=auth_pass,
        auth_remoteaddr=auth_remoteaddr,
    ), width=10)

def test_login():
    global auth_session
    _session_id = baseCall(
        'login.login',
        auth_type="ANONYMOUS",
        auth_name="",
        auth_pass="",
        login_auth_type=auth_type,
        login_auth_name=auth_name,
        login_auth_pass=auth_pass,
        auth_remoteaddr=auth_remoteaddr,
        create_session=True,# default is False
    )
    print("Session ID:", _session_id)
    if _session_id:
        auth_session = _session_id


def test_updateUserAttrs_service_price():
    from pprint import pprint
    call(
        'user.updateUserAttrs',
        user_id='1',
        attrs={
            'extra_traffic_options': '1=1234',
        },
        to_del_attrs=[],
    )
    pprint(call(
        'user.getUserInfo',
        user_id='1',
    ))


if __name__=='__main__':
    from pprint import pprint
    #pprint(call('user.getUserInfo'))  # auth_type == 'NORMAL_USER'
    #pprint(call('user.getUserInfo', user_id = sys.argv[1]))
    #pprint(call('user.getUserInfo', normal_username = sys.argv[1]))
    test_login()
    pprint(call('user.getUserInfo', user_id = "1"))


