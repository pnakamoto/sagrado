<?php
// Configurações básicas
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Define o diretório base
define('BASE_DIR', __DIR__);

// Inclui o arquivo principal do Streamlit
require_once 'sagra.py';

// Executa o aplicativo Streamlit
$command = 'streamlit run ' . BASE_DIR . '/sagra.py --server.port=8080';
exec($command);
?> 