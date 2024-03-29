#!/bin/bash

if [ -n "$1" ] ; then
	cd "$1"
fi

jd -color admin.std.json admin.json
jd -color balance.std.json balance.json
jd -color bw.std.json bw.json
jd -color charge.std.json charge.json
jd -color customer.std.json customer.json
jd -color extra_charge.std.json extra_charge.json
jd -color group.std.json group.json
jd -color import_file.std.json import_file.json
jd -color invoice.std.json invoice.json
jd -color ippool.std.json ippool.json
jd -color isp.std.json isp.json
jd -color ldap.std.json ldap.json
jd -color log_console.std.json log_console.json
jd -color login.std.json login.json
jd -color mc.std.json mc.json
jd -color notification.std.json notification.json
jd -color online_payment.std.json online_payment.json
jd -color perm.std.json perm.json
jd -color ras.std.json ras.json
jd -color report.std.json report.json
jd -color session.std.json session.json
jd -color snapshot.std.json snapshot.json
jd -color stat.std.json stat.json
jd -color SystemNotification.std.json SystemNotification.json
jd -color telephony_support.std.json telephony_support.json
jd -color user_balance.std.json user_balance.json
jd -color user_custom_field.std.json user_custom_field.json
jd -color user.std.json user.json
jd -color util.std.json util.json
jd -color voip_provider.std.json voip_provider.json
jd -color voucher.std.json voucher.json
