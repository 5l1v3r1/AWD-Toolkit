<?php
$TARGET_URL = "http://127.0.0.1";

function post($url, $data) {
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

$data = array("data" => $_POST["data"], "ip" => $_POST["ip"]);
post($TARGET_URL, $data);
?>