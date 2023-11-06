#!/bin/bash

if [ -n "$1" ] ; then
	cd "$1"
fi

delta --paging=never admin.std.json admin.json
delta --paging=never balance.std.json balance.json
delta --paging=never bw.std.json bw.json
delta --paging=never charge.std.json charge.json
delta --paging=never customer.std.json customer.json
delta --paging=never extra_charge.std.json extra_charge.json
delta --paging=never group.std.json group.json
delta --paging=never import_file.std.json import_file.json
delta --paging=never invoice.std.json invoice.json
delta --paging=never ippool.std.json ippool.json
delta --paging=never isp.std.json isp.json
delta --paging=never ldap.std.json ldap.json
delta --paging=never log_console.std.json log_console.json
delta --paging=never login.std.json login.json
delta --paging=never mc.std.json mc.json
delta --paging=never notification.std.json notification.json
delta --paging=never online_payment.std.json online_payment.json
delta --paging=never perm.std.json perm.json
delta --paging=never ras.std.json ras.json
delta --paging=never report.std.json report.json
delta --paging=never session.std.json session.json
delta --paging=never snapshot.std.json snapshot.json
delta --paging=never stat.std.json stat.json
delta --paging=never SystemNotification.std.json SystemNotification.json
delta --paging=never telephony_support.std.json telephony_support.json
delta --paging=never user_balance.std.json user_balance.json
delta --paging=never user_custom_field.std.json user_custom_field.json
delta --paging=never user.std.json user.json
delta --paging=never util.std.json util.json
delta --paging=never voip_provider.std.json voip_provider.json
delta --paging=never voucher.std.json voucher.json
