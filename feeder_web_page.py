#!/usr/bin/env python3
"""
Strona do zarządzania karmnikiem
http://raspberry-pi-ip:5000
"""

from flask import Flask, render_template_string, request, jsonify
import json
import os
import subprocess
from datetime import datetime

app = Flask(__name__)

FEEDER_DIR = '/home/admin/feeder'
CONFIG_FILE = os.path.join(FEEDER_DIR, 'config.json')
LOG_FILE = os.path.join(FEEDER_DIR, 'feeder.log')

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>wKarmnik - Panel Sterowania</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        .card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }

        .status {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin-bottom: 20px;
        }

        .status.active {
            background: #10b981;
            color: white;
        }

        .status.inactive {
            background: #ef4444;
            color: white;
        }

        .schedule-list {
            margin: 20px 0;
        }

        .schedule-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px;
            background: #f8fafc;
            border-radius: 10px;
            margin-bottom: 10px;
            transition: transform 0.2s;
        }

        .schedule-item:hover {
            transform: translateX(5px);
            background: #f1f5f9;
        }

        .schedule-time {
            font-size: 1.5em;
            font-weight: 600;
            color: #667eea;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .btn-primary {
            background: #667eea;
            color: white;
        }

        .btn-danger {
            background: #ef4444;
            color: white;
        }

        .btn-success {
            background: #10b981;
            color: white;
        }

        .btn-secondary {
            background: #64748b;
            color: white;
        }

        .btn-small {
            padding: 8px 16px;
            font-size: 0.9em;
        }

        .input-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        input[type="time"] {
            flex: 1;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 1em;
        }

        .actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }

        .log-container {
            background: #1e293b;
            color: #10b981;
            padding: 15px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
        }

        .empty-state {
            text-align: center;
            padding: 40px;
            color: #94a3b8;
        }

        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 15px 25px;
            background: #1e293b;
            color: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            display: none;
            animation: slideIn 0.3s;
        }

        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .loading {
            opacity: 0.6;
            pointer-events: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>Karmnik - Panel Sterowania</h1>
            <p class="subtitle">Zarządzaj harmonogramem karmienia</p>
            <div id="status-badge"></div>

            <div class="actions">
                <button class="btn btn-success" onclick="testFeed()">Test Karmienia</button>
                <button class="btn btn-secondary" onclick="restartService()">Restart</button>
                <button class="btn btn-primary" onclick="loadSchedules()">Odśwież</button>
            </div>
        </div>

        <div class="card">
            <h2 style="margin-bottom: 20px;">Harmonogram Karmienia</h2>

            <div class="input-group">
                <input type="time" id="newTime" placeholder="Dodaj godzinę">
                <button class="btn btn-primary" onclick="addSchedule()">Dodaj</button>
            </div>

            <div class="schedule-list" id="schedules">
                <div class="empty-state">Ładowanie...</div>
            </div>
        </div>

        <div class="card">
            <h2 style="margin-bottom: 20px;">Ostatnie Logi</h2>
            <div class="log-container" id="logs">
                Ładowanie logów...
            </div>
        </div>
    </div>

    <div class="toast" id="toast"></div>

    <script>
        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.display = 'block';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 3000);
        }

        async function loadSchedules() {
            try {
                const response = await fetch('/api/schedules');
                const data = await response.json();

                const container = document.getElementById('schedules');
                if (data.schedules.length === 0) {
                    container.innerHTML = '<div class="empty-state">Brak harmonogramu. Dodaj pierwszą godzinę!</div>';
                } else {
                    container.innerHTML = data.schedules.map(time => `
                        <div class="schedule-item">
                            <span class="schedule-time">${time}</span>
                            <button class="btn btn-danger btn-small" onclick="removeSchedule('${time}')">
                                Usuń
                            </button>
                        </div>
                    `).join('');
                }
            } catch (error) {
                showToast('Błąd wczytywania harmonogramu');
            }
        }

        async function addSchedule() {
            const timeInput = document.getElementById('newTime');
            const time = timeInput.value;

            if (!time) {
                showToast('Wybierz godzinę');
                return;
            }

            try {
                const response = await fetch('/api/schedules', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({time: time})
                });

                const data = await response.json();
                if (data.success) {
                    showToast('Dodano: ' + time);
                    timeInput.value = '';
                    loadSchedules();
                } else {
                    showToast(data.message);
                }
            } catch (error) {
                showToast('Błąd dodawania');
            }
        }

            try {
                const response = await fetch('/api/schedules', {
                    method: 'DELETE',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({time: time})
                });

                const data = await response.json();
                if (data.success) {
                    showToast('Usunięto: ' + time);
                    loadSchedules();
                } else {
                    showToast(data.message);
                }
            } catch (error) {
                showToast('Błąd usuwania');
            }
        }

        async function testFeed() {
            showToast('Testowanie karmienia...');
            try {
                const response = await fetch('/api/test');
                const data = await response.json();
                if (data.success) {
                    showToast('Test zakończony pomyślnie!');
                } else {
                    showToast('Test nie powiódł się');
                }
            } catch (error) {
                showToast('Błąd testu');
            }
        }

        async function restartService() {
            if (!confirm('Zrestartować karmnik?')) return;

            showToast('Restartowanie...');
            try {
                const response = await fetch('/api/restart', {method: 'POST'});
                const data = await response.json();
                if (data.success) {
                    showToast('Karmnik zrestartowany');
                    setTimeout(loadStatus, 2000);
                } else {
                    showToast('Błąd restartu');
                }
            } catch (error) {
                showToast('Błąd restartu');
            }
        }

        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                const badge = document.getElementById('status-badge');
                if (data.active) {
                    badge.innerHTML = '<span class="status active">Aktywny</span>';
                } else {
                    badge.innerHTML = '<span class="status inactive">Nieaktywny</span>';
                }
            } catch (error) {
                console.error('Błąd status');
            }
        }

        async function loadLogs() {
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                document.getElementById('logs').textContent = data.logs || 'Brak logów';
            } catch (error) {
                document.getElementById('logs').textContent = 'Błąd wczytywania logów';
            }
        }

        // Auto-refresh
        setInterval(() => {
            loadStatus();
            loadLogs();
        }, 5000);

        // Initial load
        loadSchedules();
        loadStatus();
        loadLogs();
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return jsonify({'success': True, 'schedules': sorted(config.get('schedules', []))})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/schedules', methods=['POST'])
def add_schedule():
    try:
        data = request.json
        time = data.get('time')

        if not time:
            return jsonify({'success': False, 'message': 'Brak godziny'})

        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        if time in config['schedules']:
            return jsonify({'success': False, 'message': 'Godzina już istnieje'})

        config['schedules'].append(time)
        config['schedules'].sort()

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        subprocess.run(['sudo', 'systemctl', 'restart', 'feeder.service'])

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/schedules', methods=['DELETE'])
def remove_schedule():
    try:
        data = request.json
        time = data.get('time')

        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        if time in config['schedules']:
            config['schedules'].remove(time)

            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)

            subprocess.run(['sudo', 'systemctl', 'restart', 'feeder.service'])

            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Godzina nie istnieje'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/test', methods=['GET'])
def test_feed():
    try:
        result = subprocess.run(
            ['python3', '-c', 'from feeder_simple import SimpleFeeder; f = SimpleFeeder(); f.feed()'],
            cwd=FEEDER_DIR,
            capture_output=True,
            timeout=10
        )
        return jsonify({'success': result.returncode == 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/restart', methods=['POST'])
def restart_service():
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'feeder.service'])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'feeder.service'],
            capture_output=True,
            text=True
        )
        active = result.stdout.strip() == 'active'
        return jsonify({'success': True, 'active': active})
    except Exception as e:
        return jsonify({'success': False, 'active': False})


@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'feeder.service', '-n', '20', '--no-pager'],
            capture_output=True,
            text=True
        )
        return jsonify({'success': True, 'logs': result.stdout})
    except Exception as e:
        return jsonify({'success': False, 'logs': str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
