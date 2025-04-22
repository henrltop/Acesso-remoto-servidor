import os
import paramiko
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
logger.debug("Tentando carregar o arquivo .env")

class SSHConnection:
    def __init__(self):
        # Valores fixos para o servidor
        self.host = "10.1.141.43"
        self.port = 22
        self.username = "ifmt"
        self.password = "mudar@123"
        self.key_path = None
        
        logger.debug(f"Usando valores fixos: HOST={self.host}, PORT={self.port}, USER={self.username}")
        
        self.client = None
        self.sftp = None
    
    def connect(self):
        try:
            logger.debug(f"Iniciando conexão SSH para {self.host}:{self.port}")
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            logger.debug("Tentando autenticar...")
            if self.key_path:
                logger.debug(f"Usando autenticação por chave: {self.key_path}")
                private_key = paramiko.RSAKey.from_private_key_file(self.key_path)
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    pkey=private_key,
                    timeout=10
                )
            else:
                logger.debug("Usando autenticação por senha")
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=10
                )
            
            logger.debug("Conexão SSH estabelecida com sucesso")
            self.sftp = self.client.open_sftp()
            logger.debug("Canal SFTP aberto com sucesso")
            return True
        except Exception as e:
            logger.error(f"ERRO DETALHADO NA CONEXÃO SSH: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            return False
    
    def disconnect(self):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
    
    def list_directory(self, path='.'):
        """Lista arquivos e diretórios no caminho especificado"""
        try:
            if not self.sftp:
                self.connect()
            
            items = self.sftp.listdir_attr(path)
            files = []
            
            for item in items:
                file_type = 'dir' if self.is_directory(item) else 'file'
                files.append({
                    'name': item.filename,
                    'type': file_type,
                    'size': item.st_size,
                    'modified': item.st_mtime,
                    'permissions': oct(item.st_mode)[-4:],  # Permissões no formato octal
                })
            
            return files
        except Exception as e:
            logger.error(f"Erro ao listar diretório: {str(e)}")
            return []
    
    def is_directory(self, item):
        """Verifica se o item é um diretório pelo modo"""
        return item.st_mode & 0o40000  # Verifica flag de diretório (S_IFDIR)
    
    def read_file(self, path):
        """Lê conteúdo de um arquivo"""
        try:
            if not self.sftp:
                self.connect()
                
            with self.sftp.file(path, 'r') as f:
                return f.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao ler arquivo: {str(e)}")
            return None
    
    def write_file(self, path, content):
        """Escreve conteúdo em um arquivo"""
        try:
            if not self.sftp:
                self.connect()
                
            with self.sftp.file(path, 'w') as f:
                f.write(content.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Erro ao escrever no arquivo: {str(e)}")
            return False
    
    def create_directory(self, path):
        """Cria um novo diretório"""
        try:
            if not self.sftp:
                self.connect()
                
            self.sftp.mkdir(path)
            return True
        except Exception as e:
            logger.error(f"Erro ao criar diretório: {str(e)}")
            return False
    
    def delete_file(self, path):
        """Remove um arquivo"""
        try:
            if not self.sftp:
                self.connect()
                
            self.sftp.remove(path)
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo: {str(e)}")
            return False
    
    def delete_directory(self, path):
        """Remove um diretório"""
        try:
            if not self.sftp:
                self.connect()
                
            self.sftp.rmdir(path)
            return True
        except Exception as e:
            logger.error(f"Erro ao remover diretório: {str(e)}")
            return False
    
    def rename(self, old_path, new_path):
        """Renomeia um arquivo ou diretório"""
        try:
            if not self.sftp:
                self.connect()
                
            self.sftp.rename(old_path, new_path)
            return True
        except Exception as e:
            logger.error(f"Erro ao renomear: {str(e)}")
            return False