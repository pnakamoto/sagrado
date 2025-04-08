# Sistema de Reabilitação SAGRA

Sistema para monitoramento e gerenciamento da reabilitação de atletas.

## Requisitos

- Python 3.8 ou superior
- cPanel com suporte a Python
- Acesso SSH (opcional, mas recomendado)

## Instalação no cPanel

1. Faça upload dos arquivos para o seu servidor via File Manager do cPanel
2. Crie um ambiente virtual Python:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure as permissões:
   ```bash
   chmod 755 sagra.py
   chmod 755 index.php
   chmod 755 .htaccess
   ```
5. Crie os diretórios necessários:
   ```bash
   mkdir planilhas_originais
   mkdir exportacoes
   mkdir backups
   chmod 777 planilhas_originais
   chmod 777 exportacoes
   chmod 777 backups
   ```
6. Configure o Python no cPanel:
   - Acesse o "Setup Python App"
   - Crie uma nova aplicação
   - Selecione a versão do Python
   - Configure o diretório raiz
   - Adicione as variáveis de ambiente necessárias

## Configuração do Banco de Dados

1. O banco de dados será criado automaticamente na primeira execução
2. Certifique-se de que o diretório tem permissões de escrita
3. O arquivo do banco de dados será criado em `reabilitacao.db`

## Acesso

- URL: `https://seudominio.com/sagra`
- Credenciais padrão:
  - Admin: admin/admin123
  - Usuário: user/user123
  - Luiz: luiz/luizao

## Suporte

Em caso de problemas, verifique:
1. Logs de erro do Python
2. Permissões de arquivos e diretórios
3. Configurações do cPanel
4. Versão do Python instalada 