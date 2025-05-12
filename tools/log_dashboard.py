# tools/log_dashboard.py
from flask import Flask, render_template, request, jsonify
import os
import sys
import re
from datetime import datetime
import json

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.log_viewer import parse_log_line, filter_logs

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/logs')
def get_logs():
    """API endpoint to get filtered logs"""
    # Get query parameters
    log_file = request.args.get('file', '')
    level = request.args.get('level', '')
    logger = request.args.get('logger', '')
    search = request.args.get('search', '')
    show_perf = request.args.get('performance', 'false').lower() == 'true'
    
    # Find log file if not specified
    if not log_file:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.startswith('ascii_wallpaper_') and f.endswith('.log')]
            if log_files:
                # Sort by modification time, most recent first
                log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)
                log_file = os.path.join(log_dir, log_files[0])
    
    if not log_file or not os.path.exists(log_file):
        return jsonify({'error': 'No log file found', 'entries': []})
    
    # Apply filters
    entries = filter_logs(
        log_file,
        level=level if level else None,
        logger=logger if logger else None,
        search=search if search else None,
        show_perf=show_perf
    )
    
    # Convert entries for JSON
    result = []
    for entry in entries:
        if entry['timestamp']:
            entry['timestamp'] = entry['timestamp'].isoformat()
        result.append(entry)
    
    return jsonify({'file': log_file, 'entries': result})

@app.route('/api/logfiles')
def get_log_files():
    """API endpoint to get available log files"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if not os.path.exists(log_dir):
        return jsonify({'files': []})
        
    log_files = [f for f in os.listdir(log_dir) if f.startswith('ascii_wallpaper_') and f.endswith('.log')]
    log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)
    
    files = []
    for file in log_files:
        path = os.path.join(log_dir, file)
        size = os.path.getsize(path)
        mtime = datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
        
        files.append({
            'name': file,
            'path': path,
            'size': size,
            'modified': mtime
        })
    
    return jsonify({'files': files})

@app.route('/api/stats')
def get_stats():
    """API endpoint to get log statistics"""
    log_file = request.args.get('file', '')
    
    # Find log file if not specified
    if not log_file:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.startswith('ascii_wallpaper_') and f.endswith('.log')]
            if log_files:
                log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)
                log_file = os.path.join(log_dir, log_files[0])
    
    if not log_file or not os.path.exists(log_file):
        return jsonify({'error': 'No log file found'})
    
    # Read all entries
    entries = filter_logs(log_file)
    
    # Compute statistics
    level_counts = {}
    logger_counts = {}
    error_messages = []
    performance_data = {}
    
    for entry in entries:
        # Level counts
        level = entry['level']
        level_counts[level] = level_counts.get(level, 0) + 1
        
        # Logger counts
        logger = entry['logger']
        logger_counts[logger] = logger_counts.get(logger, 0) + 1
        
        # Collect error messages
        if level in ['ERROR', 'CRITICAL']:
            error_messages.append({
                'timestamp': entry['timestamp'].isoformat() if entry['timestamp'] else None,
                'logger': logger,
                'message': entry['message']
            })
        
        # Collect performance data
        if 'performance' in logger and 'executed in' in entry['message']:
            # Extract function name and time
            match = re.search(r'(\w+) executed in (\d+\.\d+)ms', entry['message'])
            if match:
                func_name, exec_time = match.groups()
                if func_name not in performance_data:
                    performance_data[func_name] = []
                performance_data[func_name].append(float(exec_time))
    
    # Compute average performance times
    performance_summary = []
    for func, times in performance_data.items():
        if times:
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            performance_summary.append({
                'function': func,
                'avg_time': avg_time,
                'max_time': max_time,
                'min_time': min_time,
                'calls': len(times)
            })
    
    # Sort by average time (descending)
    performance_summary.sort(key=lambda x: x['avg_time'], reverse=True)
    
    return jsonify({
        'file': log_file,
        'total_entries': len(entries),
        'level_counts': level_counts,
        'logger_counts': logger_counts,
        'error_count': len(error_messages),
        'errors': error_messages[:10],  # Just the first 10
        'performance': performance_summary[:10]  # Top 10 performance items
    })

if __name__ == '__main__':
    # Check if log directory exists
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if not os.path.exists(log_dir):
        print(f"Log directory not found: {log_dir}")
        print("Run the application first to generate log files")
        sys.exit(1)
    
    print("Starting Log Analysis Dashboard")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True)