# SSH File Manager

Interface web para gerenciamento de arquivos via SSH com visual moderno e intuitivo.

## Sobre o Projeto

SSH File Manager é uma aplicação Django que permite gerenciar arquivos remotamente através de conexão SSH via interface web. Com design responsivo e moderno, oferece funcionalidades para:

- Navegação por diretórios
- Edição de arquivos com destacamento de sintaxe
- Upload e download de arquivos
- Criação e exclusão de diretórios
- Renomeação de arquivos e pastas
- Visualização de permissões

## Requisitos

- Python 3.8+
- Django 5.0+
- Conexão SSH a um servidor remoto

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/visual_SSH.git
   cd visual_SSH
   ```

2. Crie um ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate  # Windows
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Configure as credenciais SSH:
   ```
   # Edite o arquivo keys.env com suas credenciais
   SSH_HOST=seu_servidor
   SSH_PORT=22
   SSH_USERNAME=seu_usuario
   SSH_PASSWORD=sua_senha
   # ou use SSH_KEY_PATH para autenticação por chave
   ```

5. Execute as migrações:
   ```
   cd ssh_file_manager
   python manage.py migrate
   ```

6. Inicie o servidor:
   ```
   python manage.py runserver
   ```

7. Acesse no navegador:
   ```
   http://localhost:8000
   ```

## Funcionalidades

- **Navegação intuitiva**: Interface simples e moderna para navegar pelos diretórios
- **Editor de código**: Editor com highlighting de sintaxe para mais de 10 linguagens
- **Temas**: Suporte a tema claro/escuro com personalização
- **Segurança**: Gerenciamento de permissões e confirmação para operações críticas
- **Responsividade**: Interface adaptada para dispositivos móveis

## Tecnologias

- Django (Backend)
- Bootstrap 5 (Frontend)
- CodeMirror (Editor de código)
- Paramiko (Conexão SSH)
- jQuery (Interações AJAX)
- Font Awesome (Ícones)

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Autor

Desenvolvido por Henritop
