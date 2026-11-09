<h2>Upload</h2>
<form method="post" enctype="multipart/form-data">
  <input type="file" name="f"> <button>Upload</button>
</form>
<?php
if (!empty($_FILES['f'])) {
    $name = basename($_FILES['f']['name']);
    $type = $_FILES['f']['type'];
    // VULN: trusts client-supplied Content-Type and only checks the extension contains an image word.
    $allowed = ['image/jpeg', 'image/png', 'image/gif'];
    if (!in_array($type, $allowed)) {
        echo "<p>Only images allowed (got $type).</p>";
    } elseif (preg_match('/\.php$/i', $name)) {
        echo "<p>PHP files are not allowed.</p>"; // VULN: blocklist misses .phtml, .php5, .pHp7 etc.
    } else {
        move_uploaded_file($_FILES['f']['tmp_name'], __DIR__ . "/uploads/" . $name);
        echo "<p>Uploaded: <a href='uploads/" . htmlspecialchars($name) . "'>uploads/" . htmlspecialchars($name) . "</a></p>";
    }
}
?>
