import psutil
import platform
import time
from datetime import datetime
import json
from django.shortcuts import render
from django.utils.timezone import localtime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

from file_manager.ssh_connection import SSHConnection

def get_size(bytes):
    """
    Converte bytes para formato legível (KB, MB, GB, etc)
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}B"
        bytes /= factor

def monitoring_dashboard(request):
    """
    View para a página de monitoramento do sistema
    """
    # CPU
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_info = platform.processor() or "Não disponível"
    
    # Memória
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    memory_total = get_size(memory.total)
    memory_used = get_size(memory.used)
    
    # Disco
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    disk_total = get_size(disk.total)
    disk_used = get_size(disk.used)
    
    # Informações de partições
    disks = []
    for part in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'cdrom' in part.opts or part.fstype == '':
                continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                'device': part.device,
                'mountpoint': part.mountpoint,
                'fstype': part.fstype,
                'total': get_size(usage.total),
                'used': get_size(usage.used),
                'percent': usage.percent
            })
        except PermissionError:
            continue
    
    # Rede
    try:
        net_io = psutil.net_io_counters()
        network_tx = get_size(net_io.bytes_sent)
        network_rx = get_size(net_io.bytes_recv)
        network_throughput = get_size(net_io.bytes_sent + net_io.bytes_recv)
    except:
        network_tx = "N/A"
        network_rx = "N/A"
        network_throughput = "N/A"
    
    # Sistema Operacional
    os_info = f"{platform.system()} {platform.release()}"
    hostname = platform.node()
    
    # Uptime
    uptime_seconds = int(time.time() - psutil.boot_time())
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime = f"{days}d {hours}h {minutes}m {seconds}s"
    
    # Usuários conectados
    users = psutil.users()
    users_count = len(users)
    
    # Processos
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            pinfo = proc.info
            processes.append({
                'pid': pinfo['pid'],
                'name': pinfo['name'][:20],
                'user': pinfo['username'][:10] if pinfo['username'] else "N/A",
                'cpu': f"{pinfo['cpu_percent']:.1f}",
                'memory': f"{pinfo['memory_percent']:.1f}"
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Ordenar por uso de CPU (decrescente)
    processes = sorted(processes, key=lambda x: float(x['cpu']), reverse=True)[:15]
    processes_count = len(processes)
    
    # Temperatura (se disponível)
    temperatures = []
    if hasattr(psutil, "sensors_temperatures"):
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                for entry in entries:
                    temperatures.append({
                        'name': name if not entry.label else entry.label,
                        'value': round(entry.current)
                    })
    
    # Dados do histórico (simulados para este exemplo)
    # Em produção, você poderia armazenar esses dados em uma base de dados
    chart_labels = json.dumps([f"{i}min" for i in range(15, 0, -1)])
    cpu_history = json.dumps([
        round(min(100, max(0, cpu_usage + ((i - 7) * 5)))) for i in range(15)
    ])
    memory_history = json.dumps([
        round(min(100, max(0, memory_usage + ((i - 7) * 3)))) for i in range(15)
    ])
    
    # Data e hora da atualização
    last_update = localtime().strftime("%d/%m/%Y %H:%M:%S")
    
    context = {
        'cpu_usage': cpu_usage,
        'cpu_info': cpu_info,
        'memory_usage': memory_usage,
        'memory_total': memory_total,
        'memory_used': memory_used,
        'disk_usage': disk_usage,
        'disk_total': disk_total,
        'disk_used': disk_used,
        'disks': disks,
        'network_throughput': network_throughput,
        'network_tx': network_tx,
        'network_rx': network_rx,
        'os_info': os_info,
        'hostname': hostname,
        'uptime': uptime,
        'users_count': users_count,
        'processes': processes,
        'processes_count': processes_count,
        'temperatures': temperatures,
        'chart_labels': chart_labels,
        'cpu_history': cpu_history,
        'memory_history': memory_history,
        'last_update': last_update
    }
    
    return render(request, 'monitoring/dashboard.html', context)

@csrf_exempt
def get_server_stats(request):
    """API para obter estatísticas do servidor"""
    ssh = SSHConnection()
    
    if not ssh.connect():
        return JsonResponse({'success': False, 'error': 'Falha na conexão SSH'})
    
    try:
        # Comando para obter CPU, RAM e disco
        commands = [
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'",  # CPU usage
            "free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2}'",  # RAM usage %
            "free -m | awk 'NR==2{printf \"%d,%d\", $3, $2}'",     # RAM used,total
            "df -h / | awk 'NR==2{print $5}'",                     # Disk usage %
            "df -h / | awk 'NR==2{print $3\",\"$2}'",              # Disk used,total
            "uptime -p",                                           # Uptime
            "who | wc -l"                                          # Active users
        ]
        
        results = {}
        for cmd_name, command in zip(['cpu', 'ram_percent', 'ram', 'disk_percent', 'disk', 'uptime', 'users'], commands):
            stdin, stdout, stderr = ssh.client.exec_command(command)
            result = stdout.read().decode('utf-8').strip()
            results[cmd_name] = result
        
        # Parse RAM used,total
        ram_parts = results['ram'].split(',')
        if len(ram_parts) == 2:
            results['ram_used'] = ram_parts[0]
            results['ram_total'] = ram_parts[1]
        
        # Parse Disk used,total
        disk_parts = results['disk'].split(',')
        if len(disk_parts) == 2:
            results['disk_used'] = disk_parts[0]
            results['disk_total'] = disk_parts[1]
        
        # Get current system load
        stdin, stdout, stderr = ssh.client.exec_command("cat /proc/loadavg")
        load = stdout.read().decode('utf-8').strip().split()[:3]
        results['load'] = load
        
        # Get running processes count
        stdin, stdout, stderr = ssh.client.exec_command("ps aux | wc -l")
        results['processes'] = stdout.read().decode('utf-8').strip()
        
        # Get network stats
        stdin, stdout, stderr = ssh.client.exec_command("cat /proc/net/dev | grep -v 'lo' | awk '{if(NR>2) {print $1,$2,$10}}'")
        network_data = stdout.read().decode('utf-8').strip().split('\n')
        results['network'] = []
        
        for line in network_data:
            if line:
                parts = line.split()
                if len(parts) >= 3:
                    interface = parts[0].strip(':')
                    received = int(parts[1])
                    transmitted = int(parts[2])
                    results['network'].append({
                        'interface': interface,
                        'received': received,
                        'transmitted': transmitted
                    })
        
        # Success response
        return JsonResponse({
            'success': True, 
            'timestamp': int(time.time()),
            'data': results
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    finally:
        ssh.disconnect()

@csrf_exempt
def get_process_list(request):
    """API para obter lista de processos ativos"""
    ssh = SSHConnection()
    
    if not ssh.connect():
        return JsonResponse({'success': False, 'error': 'Falha na conexão SSH'})
    
    try:
        # Comando para obter lista de processos
        command = "ps aux | head -20"  # Limitar a 20 processos para não sobrecarregar
        stdin, stdout, stderr = ssh.client.exec_command(command)
        output = stdout.read().decode('utf-8')
        
        # Processar saída do ps aux
        lines = output.strip().split('\n')
        headers = [h.strip() for h in lines[0].split()]
        processes = []
        
        # Apenas adicionar processos (pular cabeçalho)
        for line in lines[1:]:
            parts = line.split(None, len(headers) - 1)
            process = {}
            for i, header in enumerate(headers):
                if i < len(parts):
                    process[header.lower()] = parts[i]
            processes.append(process)
        
        return JsonResponse({
            'success': True,
            'processes': processes
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    finally:
        ssh.disconnect()