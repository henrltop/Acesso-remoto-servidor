from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import tempfile
import time
import subprocess
from threading import Thread

from .ssh_connection import SSHConnection

@csrf_exempt
def execute_code(request):
    """API para executar código remotamente"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', '')
        path = data.get('path', '')
        
        if not code or not language:
            return JsonResponse({'success': False, 'error': 'Código ou linguagem não especificados'})
        
        ssh = SSHConnection()
        if not ssh.connect():
            return JsonResponse({'success': False, 'error': 'Falha na conexão SSH'})
        
        # Salvar o código temporariamente no servidor, se necessário
        # Para alguns casos, podemos executar diretamente sem salvar
        
        # Comando para executar com base na linguagem
        command = ''
        temp_file = None
        
        try:
            if language == 'python':
                # Executar código Python
                temp_file = f'/tmp/temp_exec_{int(time.time())}.py'
                
                # Escrever o código no arquivo temporário
                with ssh.sftp.file(temp_file, 'w') as f:
                    f.write(code.encode('utf-8'))
                
                # Configurar comando de execução
                command = f'python3 {temp_file} 2>&1'
                
            elif language == 'javascript':
                # Executar código JavaScript via Node.js
                temp_file = f'/tmp/temp_exec_{int(time.time())}.js'
                
                with ssh.sftp.file(temp_file, 'w') as f:
                    f.write(code.encode('utf-8'))
                
                command = f'node {temp_file} 2>&1'
                
            elif language == 'bash':
                # Executar shell script
                temp_file = f'/tmp/temp_exec_{int(time.time())}.sh'
                
                with ssh.sftp.file(temp_file, 'w') as f:
                    f.write(code.encode('utf-8'))
                
                # Tornar o script executável
                ssh.client.exec_command(f'chmod +x {temp_file}')
                command = f'bash {temp_file} 2>&1'
                
            elif language == 'php':
                # Executar código PHP
                temp_file = f'/tmp/temp_exec_{int(time.time())}.php'
                
                with ssh.sftp.file(temp_file, 'w') as f:
                    f.write(code.encode('utf-8'))
                
                command = f'php {temp_file} 2>&1'
                
            else:
                # Linguagem não suportada
                return JsonResponse({
                    'success': False, 
                    'error': f'Linguagem não suportada: {language}'
                })
            
            # Executar o comando com timeout de 10 segundos
            stdin, stdout, stderr = ssh.client.exec_command(command, timeout=10)
            
            # Ler a saída
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            # Remover arquivo temporário
            if temp_file:
                ssh.client.exec_command(f'rm -f {temp_file}')
            
            # Verificar se houve erro
            if error:
                return JsonResponse({
                    'success': True,
                    'output': error,
                    'error': True
                })
            
            return JsonResponse({
                'success': True,
                'output': output,
                'error': False
            })
            
        except Exception as e:
            # Remover arquivo temporário em caso de erro
            if temp_file:
                try:
                    ssh.client.exec_command(f'rm -f {temp_file}')
                except:
                    pass
            
            return JsonResponse({
                'success': False,
                'error': f'Erro ao executar código: {str(e)}'
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def execute_code_view(request, path):
    """Página para executar código"""
    ssh = SSHConnection()
    
    if ssh.connect():
        content = ssh.read_file(path)
        ssh.disconnect()
        
        if content is not None:
            # Determinar a linguagem pelo tipo de arquivo
            filename = os.path.basename(path)
            extension = filename.split('.')[-1].lower()
            
            language_map = {
                'py': 'python',
                'js': 'javascript',
                'sh': 'bash',
                'php': 'php',
                'html': 'html',
                'css': 'css',
                'txt': 'text',
                'json': 'json',
                'md': 'markdown',
                'xml': 'xml',
                'yml': 'yaml',
                'yaml': 'yaml'
            }
            
            language = language_map.get(extension, 'text')
            
            context = {
                'path': path,
                'filename': filename,
                'content': content,
                'language': language,
                'can_execute': language in ['python', 'javascript', 'bash', 'php']
            }
            
            return render(request, 'file_manager/execute.html', context)
        else:
            return redirect('index')
    else:
        return redirect('index')