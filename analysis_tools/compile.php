<?php
  $handle = fopen($argv[1], "r");

  if ($handle) {
    while (($line = fgets($handle)) !== false) {
      $line = trim($line);
      opcache_compile_file($line);
    }
    fclose($handle);
  }
?>
