from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import json
import os

from .ssh_connection import SSHConnection

def index(request):
    """Página inicial com o navegador de arquivos"""
    ssh = SSHConnection()
    
    current_path = request.GET.get('path', '.')
    if ssh.connect():
        files = ssh.list_directory(current_path)
        ssh.disconnect()
        
        # Organiza arquivos (diretórios primeiro, depois arquivos)
        directories = [f for f in files if f['type'] == 'dir']
        regular_files = [f for f in files if f['type'] == 'file']
        
        # Ordena por nome
        directories.sort(key=lambda x: x['name'])
        regular_files.sort(key=lambda x: x['name'])
        
        # Combina as listas
        sorted_files = directories + regular_files
        
        # Prepara caminho para navegação
        path_parts = []
        if current_path != '.':
            parts = current_path.split('/')
            for i, part in enumerate(parts):
                if part:
                    path_parts.append({
                        'name': part,
                        'path': '/'.join(parts[:i+1])
                    })
        
        context = {
            'files': sorted_files,
            'current_path': current_path,
            'path_parts': path_parts,
            'parent_path': os.path.dirname(current_path) if current_path != '.' else '.'
        }
        return render(request, 'file_manager/index.html', context)
    else:
        messages.error(request, "Não foi possível conectar ao servidor SSH.")
        return render(request, 'file_manager/index.html', {'error': 'Falha na conexão SSH'})

def edit_file(request, path):
    """Página para editar arquivos"""
    ssh = SSHConnection()
    
    if request.method == 'POST':
        content = request.POST.get('content', '')
        if ssh.connect():
            success = ssh.write_file(path, content)
            ssh.disconnect()
            
            if success:
                messages.success(request, "Arquivo salvo com sucesso!")
            else:
                messages.error(request, "Erro ao salvar o arquivo.")
            
            return redirect('edit_file', path=path)
    
    # Método GET ou erro no POST
    if ssh.connect():
        content = ssh.read_file(path)
        ssh.disconnect()
        
        if content is not None:
            context = {
                'path': path,
                'filename': os.path.basename(path),
                'content': content
            }
            return render(request, 'file_manager/edit.html', context)
        else:
            messages.error(request, "Não foi possível ler o arquivo.")
            return redirect('index')
    else:
        messages.error(request, "Não foi possível conectar ao servidor SSH.")
        return redirect('index')

@csrf_exempt
def api_file_operations(request):
    """API para operações em arquivos"""
    ssh = SSHConnection()
    
    if not ssh.connect():
        return JsonResponse({'success': False, 'error': 'Falha na conexão SSH'})
    
    operation = request.POST.get('operation')
    path = request.POST.get('path')
    result = {'success': False}
    
    try:
        if operation == 'create_directory':
            new_dir = request.POST.get('name')
            full_path = os.path.join(path, new_dir)
            result['success'] = ssh.create_directory(full_path)
            
        elif operation == 'delete_file':
            result['success'] = ssh.delete_file(path)
            
        elif operation == 'delete_directory':
            result['success'] = ssh.delete_directory(path)
            
        elif operation == 'rename':
            new_name = request.POST.get('new_name')
            old_path = path
            new_path = os.path.join(os.path.dirname(path), new_name)
            result['success'] = ssh.rename(old_path, new_path)
            
        elif operation == 'upload':
            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
                destination = os.path.join(path, uploaded_file.name)
                
                # Lê o arquivo enviado
                content = uploaded_file.read()
                
                # Cria arquivo temporário local
                temp_path = f'/tmp/{uploaded_file.name}'
                with open(temp_path, 'wb') as f:
                    f.write(content)
                
                # Envia para o servidor SSH
                sftp = ssh.sftp
                sftp.put(temp_path, destination)
                
                # Remove arquivo temporário
                os.remove(temp_path)
                result['success'] = True
    except Exception as e:
        result['error'] = str(e)
    
    ssh.disconnect()
    return JsonResponse(result)

def download_file(request):
    """Download de arquivo"""
    ssh = SSHConnection()
    path = request.GET.get('path')
    
    if not path:
        return HttpResponse("Caminho não especificado", status=400)
    
    if ssh.connect():
        try:
            # Lê o arquivo do servidor SSH
            sftp = ssh.sftp
            with sftp.file(path, 'rb') as f:
                content = f.read()
            
            # Prepara resposta para download
            filename = os.path.basename(path)
            response = HttpResponse(content)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            ssh.disconnect()
            return response
        except Exception as e:
            ssh.disconnect()
            return HttpResponse(f"Erro ao baixar arquivo: {str(e)}", status=500)
    else:
        return HttpResponse("Não foi possível conectar ao servidor SSH", status=500)