<?php

# Võtame lihtsustatava lause URList
$lause = $_GET['l'];
echo $lause;

# Käivitame Pythoni skripti andes parameetritks URLi parameetri l
exec(escapeshellcmd('python syntaks.py "'.$lause.'"'), $tulemus);

# Kuvame Pythoni skripti tulemuse
echo '<pre>'; var_dump($tulemus); echo '</pre>'

?>
