<!DOCTYPE HTML>
<html>
  <head>
    <title>Vulnerable Website</title>
  <head>

<?php

  $uploaddir = 'uploads/';
  if (isset($_FILES['file'])) {
    $file = $_FILES['file'];
    $filename = $file['name'];

    $dest = $uploaddir . $_POST['path'] . $filename;
    $contents = file_get_contents($file['tmp_name']);
    if (file_put_contents($dest, $contents))
      echo "Upload successful, view your file here : <a href='/uploads/" . $filename . "'>$filename.</a>";
    else
      echo "<h3 style='color:red'>Permission Denied : You can't write in this folder.</h3>";
  }

?>

  <body>
    <h1>Upload a file</h1>
    <p>Upload a file at the path of your choice</p>

    <form method="POST" enctype='multipart/form-data' action='.'>
      <label>Path : </label>
      <input type="text" name="path" placeholder="uploads/" style='width:800px'/>

      <br/>

      <input type="hidden" name="MAX_FILE_SIZE" value="2000000" />
      <label>File : </label>
      <input type="file" name="file"/>

      <br/>
      <input type="submit" value="Upload">
    </form>

    <a href="/override_me.php">override_me</a>
  </body>
</html>

