<?php
setlocale(LC_ALL, 'et_EE.UTF-8');

$lause = $_GET['l'];
echo $lause;
$lause = preg_replace('/\'/', '',$lause);
$tulemus = shell_exec(escapeshellcmd('LC_ALL=et_EE.UTF-8 python3 syntaks.py \''.$lause.'\' arg 2>&1'));
echo '<pre>'; print_r($tulemus); echo '</pre>'
?>
