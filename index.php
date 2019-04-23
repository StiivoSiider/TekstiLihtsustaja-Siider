<?php
setlocale(LC_ALL, 'et_EE.UTF-8');

if(isset($_GET['l'])) {
    $lause = trim($_GET['l']);
    echo $lause;
    $lause = preg_replace('/\'/', '', $lause);
    $tulemus = shell_exec(escapeshellcmd('LC_ALL=et_EE.UTF-8 python3 syntaks.py \'' . $lause . '\' arg 2>&1'));
    echo '<pre>';
    print_r($tulemus);
    echo '</pre>';
} else {
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
        $lause = trim($_GET["sisend"]);
        $lause = preg_replace('/\'/', '', $lause);
        $tulemus = shell_exec(escapeshellcmd('LC_ALL=et_EE.UTF-8 python3 syntaks.py \'' . $lause . '\' arg 2>&1'));
        $lihtsustatud_lause = preg_split('/---- /', $tulemus)[1];
        print_r($lihtsustatud_lause);
        echo '</textarea></div>';
        if($_GET["debug"] == "on") {
            echo '<pre>';
            print_r(htmlspecialchars($tulemus));
            echo '</pre>';
        }
    }
    echo '</body></html>';
}
?>
