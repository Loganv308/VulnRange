<h2>Gallery</h2>
<?php
foreach (glob(__DIR__ . '/uploads/*') as $f) {
    $n = basename($f);
    // VULN: filename reflected unescaped -> stored XSS via a crafted filename
    echo "<div><a href='uploads/$n'>$n</a></div>";
}
?>
