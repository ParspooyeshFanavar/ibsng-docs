<?php

require_once("jsonrpc.inc");

class IBSjsonrpcClient {
    /*

        All request methods return an array containing exit status (TRUE or FALSE) and result

        if exit status was FALSE means that the request was failed and the second item if error message, for example:
            array(FALSE, "Access Denied")

        if exit status was TRUE, means that the request was successfull and
        the second item is an array containing result of that request, for example:
            array(TRUE, array(1, 2, 3))

    */
    
    function IBSjsonrpcClient($server_ip, $auth_name, $auth_pass, $auth_type="ADMIN", $server_port="1237", $timeout=1800){
        $this->client = new jsonrpc_client($server_ip. ':' . $server_port);

        $this->auth_name = $auth_name;
        $this->auth_pass = $auth_pass;
        $this->auth_type = $auth_type;

        $this->timeout = $timeout;
    }

    function sendRequest($server_method, $params_arr){
        /*
            Send request to $server_method, with parameters $params_arr
            $server_method: method to call ex admin.addNewAdmin
            $params_arr: an array of parameters
        */
        $params_arr["auth_name"] = $this->auth_name;
        $params_arr["auth_pass"] = $this->auth_pass;
        $params_arr["auth_type"] = $this->auth_type;
        $response = $this->client->send($server_method, $params_arr, $this->timeout);
        $result = $this->__returnResponse($response);
        unset($response);
        return $result;
    }
    function __returnResponse($response){
        if ($response == FALSE)
            return $this->__returnError("Error occured while connecting to server");
        else if ($response->faultCode() != 0)
            return $this->__returnError($response->faultString());
        else
            return $this->__returnSuccess($response->value());
    }
    function __returnError($err_str){
        return array(FALSE, $err_str);
    }

    function __returnSuccess($value){
        return array(TRUE, $value);
    }

    function getUserInfoByUserID($user_id){
        return $this->sendRequest("user.getUserInfo", array("user_id"=>(string)$user_id));
    }

    function getUserInfoByNormalUserName($normal_username){
        return $this->sendRequest("user.getUserInfo", array("normal_username"=>$normal_username));
    }

    function getBasicUserInfoByNormalUserName($normal_username){### for Zahedan Telecom, ticket 34083
        $result = $this->sendRequest("user.getUserInfo", array("normal_username"=>$normal_username));
        if(!$result[0]){
            return $result;
        }
        $info = $result[1];
        return array(
            "user_id" => $info["basic_info"]["user_id"],
            "normal_username" => $info["attrs"]["normal_username"],
            "remaining_days" => $info["remaining_days"],
            "remaining_mega_bytes" => $info["remaining_mega_bytes"],
            "credit" => $info["basic_info"]["credit"],
            "group_name" => $info["basic_info"]["group_name"]
        );
    }

    function getUserInfoByViopUserName($voip_username){
        return $this->sendRequest("user.getUserInfo", array("voip_username"=>$voip_username));
    }

    function getUserInfoBySerial($serial){
        return $this->sendRequest("user.getUserInfo", array("serial"=>$serial));
    }

    function addNewUser($count, $credit, $isp_name, $group_name, $credit_comment=""){
        return $this->sendRequest("user.addNewUsers", array(
            "count" => $count,
            "credit" => $credit,
            "isp_name" => $isp_name,
            "group_name" => $group_name,
            "credit_comment" => $credit_comment
        ));
    }

    function setUserAttribute($user_id, $attr_name, $attr_value){
        return $this->sendRequest("user.updateUserAttrs", array(
            "user_id"=>(string)$user_id,
            "attrs"=>array($attr_name=>$attr_value),
            "to_del_attrs"=>array()
        ));
    }

    function setUserAttributes($user_id, $attrs){
        return $this->sendRequest("user.updateUserAttrs", array(
            "user_id"=>(string)$user_id,
            "attrs"=>$attrs,
            "to_del_attrs"=>array()
        ));
    }

    function setUserCustomField($user_id, $field_name, $field_value){
        return $this->sendRequest("user.updateUserAttrs", array(
            "user_id"=>(string)$user_id,
            "attrs"=>array(
                "custom_fields" => array(
                    array(
                        "custom_field_$field_name" => $field_value
                    ),
                    array(),
                ),
            ),
            "to_del_attrs"=>array()
        ));
    }

    function deleteUserAttribute($user_id, $attr_name){
        return $this->sendRequest("user.updateUserAttrs", array(
            "user_id"=>(string)$user_id,
            "attrs"=>array(),
            "to_del_attrs"=>array($attr_name)
        ));
    }

    function setNormalUserAuth($user_id, $username, $password){
        return $this->setUserAttributes($user_id, array(
            "normal_user_spec" => array(
                "normal_username"=>$username,
                "normal_password"=>$password,
            )
        ));
    }

    function setVoipUserAuth($user_id, $username, $password){
        return $this->setUserAttributes($user_id, array("voip_user_spec" => array("voip_username"=>$username, "voip_password"=>$password)));
    }    

    function setUserComment($user_id, $comment){
        return $this->setUserAttribute($user_id, "comment", $comment);
    }

    function setUserRealName($user_id, $name){
        return $this->setUserAttribute($user_id, "name", $name);
    }

    function setUserSerial($user_id, $serial){
        return $this->setUserAttribute($user_id, "serial", $serial);
    }

    function setUserEmail($user_id, $email){
        return $this->setUserAttribute($user_id, "email", $email);
    }

    function setUserPhone($user_id, $phone){
        return $this->setUserAttribute($user_id, "phone", $phone);
    }

    function setUserCellPhone($user_id, $cell_phone){
        return $this->setUserAttribute($user_id, "cell_phone", $cell_phone);
    }

    function setUserBirthDate($user_id, $birth_date, $date_unit="gregorian"){
        return $this->setUserAttributes($user_id, array("birthdate" => $birth_date, "birthdate_unit" => $date_unit));
    }

    function setUserAddress($user_id, $address){
        return $this->setUserAttribute($user_id, "address", $address);
    }

    function setUserPostalCode($user_id, $postal_code){
        return $this->setUserAttribute($user_id, "postal_code", $postal_code);
    }

    function setUserCallerID($user_id, $caller_id){
        return $this->setUserAttribute($user_id, "caller_id", $caller_id);
    }

    function lockUser($user_id, $lock_reason=""){
        return $this->setUserAttributes($user_id, array("lock"=>$lock_reason));
    }

    function unlockUser($user_id){
        return $this->deleteUserAttributes($user_id, array("lock"));
    }

    function setRelExpDate($user_id, $rel_exp_date, $date_unit="Days"){
        return $this->setUserAttributes($user_id, array("rel_exp_date"=>$rel_exp_date, "rel_exp_date_unit"=>$date_unit));
    }

    function deleteRelExpDate($user_id){
        return $this->deleteUserAttributes($user_id, array("rel_exp_date"));
    }

    function setAbsExpDate($user_id, $abs_exp_date, $date_unit="gregorian"){
        return $this->setUserAttributes($user_id, array("abs_exp_date"=>$abs_exp_date, "abs_exp_date_unit"=>$date_unit));
    }

    function deleteAbsExpDate($user_id){
        return $this->deleteUserAttributes($user_id, array("abs_exp_date"));
    }

    function addRandomVoipUsers($count, $credit, $isp_name, $group_name){
        $result = $this->sendRequest("user.addNewUsers", array(
            "count" => $count,
            "credit" => $credit,
            "isp_name" => $isp_name,
            "group_name" => $group_name,
            "credit_comment" => "Random VoIP Users by CRM",
            "custom_fields" => array()
        ));
        if(!$result[0]){
            return $result;
        }
        $user_ids_list = $result[1];
        $user_ids_str = implode(",", $user_ids_list);
        return $this->sendRequest("user.updateUserAttrs", array(
            "user_id" => $user_ids_str,
            "attrs" => array(
                "voip_user_spec" => array(
                    "voip_username_random_prefix" => "",
                    "voip_username_random_length" => 7,
                    "voip_username_random_type" => 2, ## numbers only
                    "voip_password" => ""
                )
            ),
            "to_del_attrs" => array(),
        ));
    }

    function searchUser($conds){
        $result = $this->sendRequest("user.searchUser", array(
            "conds" => $conds,
            "from" => 1,
            "to" => 50000,
            "order_by" => "user_id",
            "desc" => FALSE
        ));
        if(!$result[0]){
            return $result;
        }
        return array(TRUE, $result[1][2]);
    }

    function searchNeverLoggedInUsers(){## date filter on what????
        return $this->searchUser(array("never_logged_in_users" => TRUE));
    }

    function searchUserRelExpDateTo($to_date, $date_unit="gregorian"){
        return $this->searchUser(array(
            "rel_exp_date_to" => $to_date,
            "rel_exp_value_unit" => $date_unit
        ));
    }

    function searchUserByPhone($phone){
        return $this->searchUser(array(
            "phone" => $phone,
            "phone_op" => "like",## "equals", "like", "ilike", "starts_with", "ends_with"
            'view_options' => '0',
        ));
    }

    function searchUserByCellPhone($cell_phone){
        return $this->searchUser(array(
            "cell_phone" => $cell_phone,
            "cell_phone_op" => "like",## "equals", "like", "ilike", "starts_with", "ends_with"
            'view_options' => '0',
        ));
    }

    function getUserInfoByPhone($phone){
        $result = $this->searchUserByPhone($phone);
        if(!$result[0]){
            return $result;
        }
        $user_id_list = $result[1];
        if(count($user_id_list)==0){
            return array(FALSE, "User with phone $phone not found");
        }
        return $this->getUserInfoByUserID($user_id_list[0]);
    }

    function searchUserOnlines(){
        ## Online-related conditions are added in C_ws_294
        $conds = array(
            "is_online" => TRUE,
            #"online_status" => "online",
            #"online_status" => "idle",
            #"online_status" => "failed",
            #"login_time_from" => "10", "login_time_from_unit" => "minutes",
            #"login_time_from" => "2016-04-03 17:00", "login_time_from_unit" => "gregorian",
            #"login_time_to" => "5", "login_time_from_unit" => "minutes",
            #"login_time_to" => "2016-04-03 18:00", "login_time_from_unit" => "gregorian",
            #"ras_ips" => "192.168.100.1",
        );
        $result = $this->sendRequest("user.searchUser", array(
            "conds" => $conds,
            "from" => 1,
            "to" => 50000,
            "order_by" => "user_id",
            "desc" => FALSE
        ));
        if(!$result[0]){
            return $result;
        }
        return array(TRUE, $result[1][2]);
    }

    function getAllInternetOnlineUsers(){
        $result = $this->sendRequest("report.getOnlineUsers", array(
            "conds" => array(),
            "normal_sort_by" => "user_id",
            "normal_desc" => FALSE,
            "voip_sort_by" => "user_id",
            "voip_desc" => FALSE,
        ));
        $succeed = $result[0];
        if(!$succeed){
            return $result;
        }
        $internet_onlines = $result[1][0];
        return $internet_onlines;
    }

    function getOnlineUsersWithRemoteIP(){## FIXME remote_ip
        $result = $this->sendRequest("report.getOnlineUsers", array(
            "conds" => array(),
            "normal_sort_by" => "user_id",
            "normal_desc" => FALSE,
            "voip_sort_by" => "user_id",
            "voip_desc" => FALSE,
        ));
        $succeed = $result[0];
        if(!$succeed){
            return $result;
        }
        $internet_onlines = $result[1][0];
        #$voip_onlines = $result[1][0];
        $internet_onlines_abs = array();
        foreach($internet_onlines as $user_info){
            $internet_onlines_abs[$user_info["user_id"]] = $user_info["attrs"]["remote_ip"];
        }
        return array(TRUE, $internet_onlines_abs);
    }

    function getConnectionLogs($login_time_from, $login_time_to, $user_ids=null, $remote_ip=null, $date_unit="gregorian"){
        $conds = array(
            "login_time_from" => $login_time_from,
            "login_time_from_unit" => $date_unit,
            "login_time_to" => $login_time_to,
            "login_time_to_unit" => $date_unit,
        );

        if($user_ids){
            $conds["user_ids"] = $user_ids;
        }

        if($remote_ip){
            $conds["remote_ip"] = $remote_ip;
        }

        $result = $this->sendRequest("report.getConnections", array(
            "conds" => $conds,
            "from" => 1,
            "to" => 50000,
            "sort_by" => "user_id", ## FIXME
            "desc" => FALSE
        ));

        if (!$result[0]){
            return $result;
        }

        $report = $result[1]["report"];
        $report_abs = array();

        foreach($report as $item){
            $mac = NULL;
            foreach($item["details"] as $det){
                if($det[0]=="mac"){
                    $mac = $det[1];
                    break;
                }
            }
            $report_abs[] = array(
                "user_id" => $item["user_id"],
                "login_time" => $item["login_time_formatted"],
                "logout_time" => $item["logout_time_formatted"],
                "bytes_in" => $item["bytes_in"],
                "bytes_out" => $item["bytes_out"],
                "remote_ip" => $item["remote_ip"],
                "mac" => $mac
            );
        }

        #return array(TRUE, $report_abs);
        return array(TRUE, $report);
    }

    function getConnectionLogsForMac($login_time_from, $login_time_to, $mac, $date_unit="gregorian"){
        $conds = array(
            "login_time_from" => $login_time_from,
            "login_time_from_unit" => $date_unit,
            "login_time_to" => $login_time_to,
            "login_time_to_unit" => $date_unit,
            "mac" => $mac
        );


        $result = $this->sendRequest("report.getConnections", array(
            "conds" => $conds,
            "from" => 1,
            "to" => 50000,
            "sort_by" => "login_time", ## FIXME
            "desc" => TRUE
        ));

        if (!$result[0]){
            return $result;
        }

        $report = $result[1]["report"];
        $report_abs = array();

        foreach($report as $item){
            $mac = NULL;
            foreach($item["details"] as $det){
                if($det[0]=="mac"){
                    $mac = $det[1];
                    break;
                }
            }
            $report_abs[] = array(
                "user_id" => $item["user_id"],
                "login_time" => $item["login_time_formatted"],
                "logout_time" => $item["logout_time_formatted"],
                "bytes_in" => $item["bytes_in"],
                "bytes_out" => $item["bytes_out"],
                "remote_ip" => $item["remote_ip"],
                "mac" => $mac
            );
        }

        return array(TRUE, $report_abs);
    }



    function getConnectionLogsTrafficMoreThan($more_than_bytes, $login_time_from, $login_time_to, $date_unit="gregorian"){
        $result = $this->sendRequest("report.getConnections", array(
            "conds" => array(
                "login_time_from" => $login_time_from,
                "login_time_from_unit" => $date_unit,
                "login_time_to" => $login_time_to,
                "login_time_to_unit" => $date_unit,
            ),
            "from" => 1,
            "to" => 50000,
            "sort_by" => "user_id", ## FIXME
            "desc" => FALSE
        ));

        if (!$result[0]){
            return $result;
        }

        $report = $result[1]["report"];
        $report_abs = array();

        foreach($report as $item){
            $bytes = $item["bytes_in"] + $item["bytes_out"];
            if($bytes > $more_than_bytes){
                $report_abs[] = array(
                    "user_id" => $item["user_id"],
                    "bytes" => $bytes,
                    "bytes_in" => $item["bytes_in"],
                    "bytes_out" => $item["bytes_out"],
                    "login_time" => $item["login_time_formatted"],
                    "logout_time" => $item["logout_time_formatted"],
                );
            }
        }
        return array(TRUE, $report_abs);
    }

    function killUser($user_id){
        return $this->sendRequest("user.killUserByID", array(
            "user_id"=>(string)$user_id
        ));
    }

    function setStaticIp($user_id, $ip)
    {
        return $this->setUserAttributes($user_id, ["assign_ip" => $ip]);
    }

    function unsetStaticIp($user_id)
    {
        return $this->deleteUserAttribute($user_id, "assign_ip");
    }

    function searchUserByCreationDate($creation_date_from, $creation_date_to, $date_unit="gregorian"){
        return $this->searchUser(array(
            "creation_date_from" => $creation_date_from,
            "creation_date_from_unit" => $date_unit,
            "creation_date_to" => $creation_date_to,
            "creation_date_to_unit" => $date_unit
        ));
    }

    function searchUserByCredit($credit_op, $credit){
        return $this->searchUser(array(
            "credit_op" => $credit_op,
            "credit" => $credit
        ));
    }

    function setUserCredit($user_id, $credit, $comment=""){
        return $this->sendRequest("user.changeCredit", array(
            "user_id" => $user_id,
            "credit" => $credit,
            "is_absolute_change" => TRUE,
            "credit_comment" => $comment
        ));
    }

    function addToUserCredit($user_id, $credit, $comment=""){
        return $this->sendRequest("user.changeCredit", array(
            "user_id" => $user_id,
            "credit" => $credit,
            "is_absolute_change" => FALSE,
            "credit_comment" => $comment
        ));
    }

    function setUserDeposit($user_id, $deposit, $comment=""){
        return $this->sendRequest("user.changeDeposit", array(
            "user_id" => $user_id,
            "deposit" => $deposit,
            "is_absolute_change" => TRUE,
            "deposit_comment" => $comment
        ));
    }

    function addToUserDeposit($user_id, $deposit, $comment=""){
        return $this->sendRequest("user.changeDeposit", array(
            "user_id" => $user_id,
            "deposit" => $deposit,
            "is_absolute_change" => FALSE,
            "deposit_comment" => $comment
        ));
    }
    function renewUser($user_id, $comment){
        return $this->sendRequest("user.renewUsers", array(
            "user_id" => "$user_id",
            "comment" => $comment,
        ));
    }
    function renewNextGroupUser($user_id, $group_name, $comment){
        $res = $this->setUserAttributes($user_id, array(
            "renew_next_group" => $group_name,
            "renew_remove_user_exp_dates" => true,
        ));
        if(!$res[0]){
            return $res;
        }
        return $this->renewUser($user_id, $comment);
    }
    function getUserIdByNormalUsername($username){
        $info_result = $this->getUserInfoByNormalUserName($username);
        if($info_result[0]){
            $keys = array_keys($info_result[1]);
            if(count($keys)==0){
                return array(FALSE, "No user with internet username '$username'");
            }else{
                return array(TRUE, $keys[0]);
            }
        }else{
            return $info_result;
        }
    }

    function getCreditChangesByUsername($username, $change_time_from, $change_time_to, $date_unit="gregorian"){
        $user_id_res = $this->getUserIdByNormalUsername($username);
        if(!$user_id_res[0]){
            return $user_id_res;
        }
        $user_id = $user_id_res[1];
        var_dump($user_id);
        $result = $this->sendRequest("report.getCreditChanges", array(
            "conds" => array(
                "user_ids" => "$user_id",
                "change_time_from" => $change_time_from,
                "change_time_from_unit" => $date_unit,
                "change_time_to" => $change_time_to,
                "change_time_to_unit" => $date_unit
            ),
            "from" => 1,
            "to" => 50000,
            "sort_by" => "change_time", ## FIXME
            "desc" => FALSE
        ));

        return $result;
        
        /*
        if (!$result[0]){
            return $result;
        }

        $report = $result[1]["report"];
        
        $report_abs = array();

        foreach($report as $item){
            $item_uids = $item["user_ids"];
            foreach($item_uids as $i => $item_uid){
                if($item_uid == $user_id){
                    $report_abs[] = $item;
                    break;
                }
            }
        }
        return array(TRUE, $report_abs);
        */
    }


    function changeUserGroupByUserId($user_id, $group_name){
        $this->setUserAttribute($user_id, "group_name", $group_name);
    }

    function changeUserGroupByUsername($username, $group_name){
        $user_id_res = $this->getUserIdByNormalUsername($username);
        if(!$user_id_res[0]){
            return $user_id_res;
        }
        $user_id = $user_id_res[1];
        $this->setUserAttribute($user_id, "group_name", $group_name);
    }

    function getGroupIdToGroupNameMapping(){
        $res = $this->sendRequest("group.listGroups", array());
        if(!$res[0]){
            return $res;
        }
        $map = array();
        foreach($res[1] as $group_name){
            $res = $this->sendRequest("group.getGroupInfo", array("group_name"=>$group_name));
            $group_id = $res[1]["group_id"];
            #echo "group_name=$group_name, group_id=$group_id\n";
            $map[] = array($group_id=>$group_name);
        }
        return $map;
    }

    function getGroupInfoByID($group_id){
        return $this->sendRequest("group.getGroupInfoByID", array("group_id"=>$group_id));
    }


    ####################################################################################
    ############################## Graphs ##############################################

    function getOnlineBwSnapshotForUserID($user_id){
        $info_res = $this->getUserInfoByUserID($user_id);
        if(!$info_res[0]){
            return $info_res;
        }
        $values = array_values($info_res[1]);
        $info = $values[0];
        $onlines = $info["internet_onlines"];## $online ===> (ras_ip, ras_desc, port_or_id, login_time, remote_ip)
        if(count($onlines)==0){
            return array(false, "User is not online");
        }
        return $this->sendRequest("snapshot.getBWSnapShotForUser", array(
            "user_id" => $user_id,
            "ras_ip" => $onlines[0][0],
            "unique_id_val" => $onlines[0][2],
        ));
    }

    function getOfflineBwSnapshotForUserID($user_id, $date_from, $date_to){
        return $this->sendRequest("snapshot.getBWSnapShot", array(
            "user_id" => $user_id,
            "conds" => array(
                "date_from" => $date_from,
                "date_from_unit" => "gregorian",
                "date_to" => $date_to,
                "date_to_unit" => "gregorian",
            ),
        ));
    }

    function getOnlineBwSnapshotForUserName($username){
        $info_res = $this->getUserInfoByNormalUserName($username);
        if(!$info_res[0]){
            return $info_res;
        }
        $values = array_values($info_res[1]);
        $info = $values[0];
        $onlines = $info["internet_onlines"];## $online ===> (ras_ip, ras_desc, port_or_id, login_time, remote_ip)
        if(count($onlines)==0){
            return array(false, "User is not online");
        }
        return $this->sendRequest("snapshot.getBWSnapShotForUser", array(
            "user_id" => $info["basic_info"]["user_id"],
            "ras_ip" => $onlines[0][0],
            "unique_id_val" => $onlines[0][2],
        ));

    }
    
    function getOnlineBwSnapshotForUserUnique($user_id, $ras_ip, $unique_id_val){
        return $this->sendRequest("snapshot.getBWSnapShotForUser", array(
            "user_id" => $user_id,
            "ras_ip" => $ras_ip,
            "unique_id_val" => $unique_id_val,
        ));
    }

    ###########################################################################
    ######################### Online Payment: #################################

    function getAvailablePaymentGateways(){
        return $this->sendRequest("online_payment.getAvailablePaymentGateways", array());
    }

    function preparePayment($gateway_type, $session_id, $amount, $callback_url){
        /*
            $gateway_type: one of these values:
                "Mellat-Shaparak"
                "Eghtesad_Novin" 
                "ZarinPal"
                "Saman"
                "Parsian"
                "Melli-shahparak"
                "Pasargad"
            $session_id: string, a session id generated by the website (CRM) for user
            $amount: number
        */
        return $this->sendRequest("online_payment.preparePayment", array(
            "gateway_type" => $gateway_type,
            "unique_id" => $session_id,
            "amount" => $amount,
            "attribute_map" => array("redirect_url" => $callback_url),// Only for Mellat Bank
        ));
    }

    function paymentRedirectToMellatBank($amount, $session_id, $callback_url){
        /*
            $session_id: string, a session id generated by the website (CRM) for user
            $amount: number
            $callback_url: url of the website(CRM) that the bank must redirect the user after payment
        */
        $gateway_type = "Mellat-Shaparak";
        $resp = $this->preparePayment($gateway_type, $session_id, $amount, $callback_url);
        if (! $resp[0]){// unsuccessfull
            echo "ERROR: " . $resp[1];
            return $resp;
        }
        $bank_url = $resp[1]["url"];
        $redirect_method = $resp[1]["redirect_method"];// "POST" or "GET"
        $web_attributes = $resp[1]["web_attributes"];
        #$web_attributes["redirect_url"] = $callback_url;// Only for Mellat Bank
        ###############################
        echo "
<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>
<html>
<head>
    <meta content='text/html; charset=UTF-8' http-equiv='content-type'/>
    <title>Online Payment Redirect</title>
</head>
<body>";
        #echo "Redirecting To Bank Website...";
        var_dump($web_attributes);
        echo "<form method='$redirect_method' action='$bank_url' id='redirect_form'>";
        foreach ($web_attributes as $key => $value){
            echo "<input type='hidden' name='${key}' value='${value}' />";
        }
        echo "<input type=submit value='Go to bank website'></input>";
        echo "</form>";

        #echo "<script>document.getElementById('redirect_form').submit();</script>";
        echo "</body></html>";
    }

    function verifyPaymentMellat($attrs){// Only for Mellat Bank
        return $this->sendRequest("online_payment.verifyPayment", array(
            "unique_id" => $attrs["RefId"],
            "web_attributes" => $attrs,
        ));
    }


    function paymentRedirectToENBank($amount, $session_id, $callback_url){
        /*
            $session_id: string, a session id generated by the website (CRM) for user
            $amount: number
            $callback_url: url of the website(CRM) that the bank must redirect the user after payment
        */
        $gateway_type = "Eghtesad_Novin";
        $resp = $this->preparePayment($gateway_type, $session_id, $amount, $callback_url);
        if (! $resp[0]){// unsuccessfull
            echo "ERROR: " . $resp[1];
            return $resp;
        }
        $bank_url = $resp[1]["url"];
        $redirect_method = $resp[1]["redirect_method"];// "POST" or "GET"
        $web_attributes = $resp[1]["web_attributes"];
        #$web_attributes["redirect_url"] = $callback_url;// Only for Mellat Bank
        ###############################
        echo "
<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>
<html>
<head>
    <meta content='text/html; charset=UTF-8' http-equiv='content-type'/>
    <title>Online Payment Redirect</title>
</head>
<body>";
        #echo "Redirecting To Bank Website...";
        var_dump($web_attributes);
        echo "<form method='$redirect_method' action='$bank_url' id='redirect_form'>";
        foreach ($web_attributes as $key => $value){
            echo "<input type='hidden' name='${key}' value='${value}' />";
        }
        echo "<input type=submit value='Go to bank website'></input>";
        echo "</form>";

        #echo "<script>document.getElementById('redirect_form').submit();</script>";
        echo "</body></html>";
    }

    function verifyPaymentEN($attrs){// Only for Mellat Bank
        return $this->sendRequest("online_payment.verifyPayment", array(
            "unique_id" => $attrs["ResNum"],
            "web_attributes" => $attrs,
        ));
    }

    function getSevenDaysExpiredUsers(){
        return $this->sendRequest("user.searchExpiredUsers", array(
            "conds" => array(
                  "exp_date_from" => "60",
                "exp_date_from_unit" => "days",
                "exp_date_to" => "7",
                "exp_date_to_unit" => "days",
            ),
            "from" => 0,
            "to" => 100000,
            "order_by" => "user_id",
            "desc" => false,
        ));
    }

    function setAsteriskExtention($user_id, $extension, $ras_ip){
        return $this->sendRequest("user.updateUserAttrs", array(
            "user_id"=>(string)$user_id,
            "attrs"=>array(
                "asterisk_extension" => $extension,
                "asterisk_ras_ip" => $ras_ip,
                "asterisk_sip_details" => array(
                    "port" => 5060,
                    ## and other (optional) attributes
                ),
                "asterisk_iax_details" => array(
                    "port" => 4569,
                    ## and other (optional) attributes
                ),
            ),
            "to_del_attrs"=>array()
        ));
    }

    function setUserFirstLogin($user_id, $first_login_epoch){
        return $this->sendRequest("user.updateUserAttrs", array(
            "user_id"=>(string)$user_id,
            "attrs"=>array(
                "first_login" => $first_login_epoch,
            ),
            "to_del_attrs"=>array()
        ));
    }

    function resetOneChargeRuleUsage($user_id, $charge_rule_id){
        return $this->sendRequest("user.setOneChargeRuleUsage", array(
            "user_id" => $user_id,
            "charge_rule_id" => $charge_rule_id,
            "credit_usage" => 0,
            "time_usage" => 0,
            "traffic_usage" => 0,
        ));
    }

}

?>
