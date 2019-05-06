<?php
setlocale(LC_ALL, 'et_EE.UTF-8');

/**
 * Lihtsustaja väljundi printimiseks
 *
 * @param $tulemus string   Lihtsustaja väljund
 */
function prindi($tulemus){
    echo '<pre>';
    print_r(htmlspecialchars($tulemus));
    echo '</pre>';
}

/**
 * Käsitsi sisestatud teksti eeltöötlus
 *
 * @param $lause string   Sisestatud lause
 * @return null|string|string[]   Korrastatud lause
 */
function eeltöötlus($lause){
    $lause = trim($lause);
    $lause = preg_replace('/\'/', '', $lause);
    return $lause;
}

if($_GET['random'] == "on") {
    // Juhusliku lause lihtsustamine
    prindi(shell_exec(escapeshellcmd('LC_ALL=et_EE.UTF-8 python3 random_simplify.py 2>&1')));
} else if(isset($_GET['l'])) {
    // API peafunktsioon - võtta parameetrina lause ning tagastada selle lihtsustus
    $lause = eeltöötlus($_GET['l']);
    echo $lause;
    prindi(shell_exec(escapeshellcmd('LC_ALL=et_EE.UTF-8 python3 syntaks.py \'' . $lause . '\' arg 2>&1')));
} else {
    // Lisafunktsioon
    // Veebilehena lause lihtsustamine, koostab veebilehe
    echo '<html><body>
           <div>
            <form method="get" action="';
                 echo $PHP_SELF;
                 echo '">
             <textarea rows = "5" cols = "100" name = "sisend">';
                 echo $_GET['sisend'];
                 echo '</textarea>
             <input type="submit" value="Lihtsusta"/>
             <input type="checkbox" name="debug" id="debug"';
                 if($_GET["debug"] == "on"){
                     echo ' checked';
                 }
                 echo'/>
             <label for="debug">Debug</label>
            </form>
           </div>';
    if(isset($_GET["sisend"])){
        echo '<div><textarea rows="5" cols="100" readonly>';
        $lause = eeltöötlus($_GET["sisend"]);
        $tulemus = shell_exec(escapeshellcmd('LC_ALL=et_EE.UTF-8 python3 syntaks.py \'' . $lause . '\' arg 2>&1'));
        $lihtsustatud_lause = preg_split('/---- /', $tulemus)[1];
        print_r($lihtsustatud_lause);
        echo '</textarea></div>';

        if($_GET["debug"] == "on") {
            prindi($tulemus);
        }
    }
    echo '</body></html>';
}
?>
