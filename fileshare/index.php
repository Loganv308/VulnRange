<?php
// FileShare -- INTENTIONALLY VULNERABLE. Lab use only. Never expose to the internet.
$page = $_GET['page'] ?? 'home';
?>
<!doctype html><html><head><title>FileShare</title>
<style>body{font-family:sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem}nav a{margin-right:1rem}</style></head>
<body><nav><b>FileShare</b> | <a href="?page=home">Home</a><a href="?page=upload">Upload</a><a href="?page=gallery">Gallery</a></nav><hr>
<?php
// VULN: local file inclusion. Appends .php, but php:// wrappers and other .php files still work.
include($page . '.php');
?>
</body></html>
