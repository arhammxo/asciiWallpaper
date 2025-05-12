#!/usr/bin/env python3
"""
ASCII Art Wallpaper Generator - Log Viewer
A simple utility to view and filter log files
"""

import os
import sys
import re
import argparse
from datetime import datetime

def parse_log_line(line):
    """Parse a log line into components"""
    # Basic log format: 2023-05-12 14:30:45,123 [LEVEL] logger_name:line_num - Message
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[(\w+)\] ([^:]+):(\d+)(?:\s+\(([^)]+)\))? - (.*)'
    match = re.match(pattern, line)
    
    if match:
        timestamp_str, level, logger, line_num, function, message = match.groups()
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
        except ValueError:
            timestamp = None
            
        return {
            'timestamp': timestamp,
            'level': level,
            'logger': logger,
            'line': int(line_num) if line_num else 0,
            'function': function,
            'message': message,
            'original': line
        }
    return None

def filter_logs(log_file, level=None, logger=None, search=None, start_time=None, end_time=None, show_perf=True):
    """Filter log entries based on criteria"""
    filtered_entries = []
    
    # Convert level to uppercase if provided
    if level:
        level = level.upper()
    
    # Read the log file
    try:
        with open(log_file, 'r') as f:
            for line in f:
                entry = parse_log_line(line.strip())
                if not entry:
                    continue
                    
                # Apply filters
                if level and entry['level'] != level:
                    continue
                    
                if logger and logger.lower() not in entry['logger'].lower():
                    continue
                    
                if search and search.lower() not in entry['message'].lower():
                    continue
                    
                if not show_perf and 'performance' in entry['logger'].lower():
                    continue
                    
                if start_time and entry['timestamp'] and entry['timestamp'] < start_time:
                    continue
                    
                if end_time and entry['timestamp'] and entry['timestamp'] > end_time:
                    continue
                    
                filtered_entries.append(entry)
    except Exception as e:
        print(f"Error reading log file: {e}")
        return []
        
    return filtered_entries

def display_entries(entries, colorize=True, show_full=False):
    """Display log entries with optional colorization"""
    if not entries:
        print("No matching log entries found.")
        return
        
    # Set up colors if enabled
    if colorize and sys.stdout.isatty():
        colors = {
            'DEBUG': '\033[94m',    # Blue
            'INFO': '\033[92m',     # Green
            'WARNING': '\033[93m',  # Yellow
            'ERROR': '\033[91m',    # Red
            'CRITICAL': '\033[1;91m', # Bold Red
            'RESET': '\033[0m'
        }
    else:
        colors = {level: '' for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']}
        colors['RESET'] = ''
    
    # Display entries
    for entry in entries:
        level_color = colors.get(entry['level'], '')
        reset = colors['RESET']
        
        if show_full:
            print(f"{level_color}{entry['original']}{reset}")
        else:
            timestamp = entry['timestamp'].strftime('%H:%M:%S') if entry['timestamp'] else 'UNKNOWN'
            logger_short = entry['logger'].split('.')[-1] if '.' in entry['logger'] else entry['logger']
            print(f"{timestamp} {level_color}[{entry['level']}]{reset} {logger_short}: {entry['message']}")

def main():
    parser = argparse.ArgumentParser(description='ASCII Art Wallpaper Generator - Log Viewer')
    parser.add_argument('-f', '--file', help='Log file to read (defaults to most recent)')
    parser.add_argument('-l', '--level', help='Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('-m', '--module', help='Filter by module/logger name')
    parser.add_argument('-s', '--search', help='Search text in message')
    parser.add_argument('-p', '--performance', action='store_true', help='Show performance logs (hidden by default)')
    parser.add_argument('--no-color', action='store_true', help='Disable colorized output')
    parser.add_argument('--full', action='store_true', help='Show full log entries')
    
    args = parser.parse_args()
    
    # Find log file if not specified
    log_file = args.file
    if not log_file:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.startswith('ascii_wallpaper_') and f.endswith('.log')]
            if log_files:
                # Sort by modification time, most recent first
                log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)
                log_file = os.path.join(log_dir, log_files[0])
    
    if not log_file or not os.path.exists(log_file):
        print("Error: No log file found")
        return 1
        
    print(f"Reading log file: {log_file}")
    
    # Apply filters and display
    entries = filter_logs(
        log_file,
        level=args.level,
        logger=args.module,
        search=args.search,
        show_perf=args.performance
    )
    
    display_entries(
        entries, 
        colorize=not args.no_color,
        show_full=args.full
    )
    
    print(f"\nTotal entries displayed: {len(entries)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())