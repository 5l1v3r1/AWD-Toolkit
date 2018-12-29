<?php
$PRIVATEKEY_PATH = "private.pem";
$RECORD_PATH = "record.txt";
date_default_timezone_set('PRC');

function decrypt($content) {
    global $PRIVATEKEY_PATH;
    $prikey = openssl_pkey_get_private(file_get_contents($PRIVATEKEY_PATH));
    openssl_private_decrypt($content, $decrypted, $prikey);
    return $decrypted;
}

$data = decrypt(base64_decode($_POST["data"]));
$ip = $_POST["ip"];

$data = json_encode(array("data" => $data, "ip" => $ip, "ts" => time(), "time" => date('H:i:s')));
$fd = fopen($RECORD_PATH, "a");
fwrite($fd, $data);
fwrite($fd, "\n");
fclose($handle);
?>