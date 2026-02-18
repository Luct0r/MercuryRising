#!/usr/bin/env python3
"""
Email Sender Script
Randomly selects credentials and messages, then sends emails with random delays.
Supports progressive sending (1 email day 1, 2 day 2, etc.) and automatic crontab management.
"""

import json
import random
import time
import subprocess
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta

def load_history():
    """Load sending history from history.json file."""
    history_file = Path(__file__).parent / 'history.json'
    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            pass
    return {"start_date": None, "daily_sends": {}}

def save_history(history):
    """Save sending history to history.json file."""
    history_file = Path(__file__).parent / 'history.json'
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

def get_current_day_info(history):
    """Get current day number and emails to send today."""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not history["start_date"]:
        # First run - initialize
        history["start_date"] = today
        day_number = 1
    else:
        start_date = datetime.strptime(history["start_date"], '%Y-%m-%d')
        current_date = datetime.strptime(today, '%Y-%m-%d')
        day_number = (current_date - start_date).days + 1
    
    # Check if we've already sent emails today
    emails_sent_today = history["daily_sends"].get(today, 0)
    emails_to_send = max(0, day_number - emails_sent_today)
    
    return day_number, emails_to_send, today

def update_history(history, date, count):
    """Update history with emails sent."""
    history["daily_sends"][date] = history["daily_sends"].get(date, 0) + count
    save_history(history)

def setup_crontab():
    """Set up crontab for daily execution."""
    script_path = Path(__file__).resolve()
    cron_command = f"0 10 * * * /usr/bin/python3 {script_path}"
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        
        # Check if our job already exists
        if str(script_path) in current_cron:
            print("Crontab entry already exists.")
            return True
        
        # Add our cron job
        new_cron = current_cron.rstrip() + f"\n{cron_command}\n" if current_cron else f"{cron_command}\n"
        
        # Set the new crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
        
        if process.returncode == 0:
            print(f"✓ Crontab set up successfully: {cron_command}")
            return True
        else:
            print("✗ Failed to set up crontab")
            return False
            
    except Exception as e:
        print(f"✗ Error setting up crontab: {e}")
        return False

def remove_crontab():
    """Remove our crontab entry."""
    script_path = Path(__file__).resolve()
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("No crontab to remove.")
            return True
        
        current_cron = result.stdout
        
        # Remove lines containing our script path
        new_lines = []
        removed = False
        for line in current_cron.split('\n'):
            if str(script_path) not in line:
                if line.strip():  # Only add non-empty lines
                    new_lines.append(line)
            else:
                removed = True
        
        if not removed:
            print("Crontab entry not found.")
            return True
        
        # Set the new crontab (or remove it entirely if empty)
        if new_lines:
            new_cron = '\n'.join(new_lines) + '\n'
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_cron)
        else:
            # Remove crontab entirely if no entries left
            subprocess.run(['crontab', '-r'], capture_output=True)
        
        print("✓ Crontab entry removed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error removing crontab: {e}")
        return False

def check_and_cleanup_crontab(history):
    """Check if 5 days have passed and remove crontab if so."""
    if not history["start_date"]:
        return
    
    start_date = datetime.strptime(history["start_date"], '%Y-%m-%d')
    current_date = datetime.now()
    days_passed = (current_date - start_date).days + 1
    
    if days_passed > 5:
        print(f"5 days completed (day {days_passed}). Removing crontab...")
        remove_crontab()

def load_json_file(filename):
    """Load and parse a JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: {filename} contains invalid JSON.")
        return None
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None

def send_email(sender_email, sender_password, sender_display_name, recipient_email, subject, body):
    """Send an email using swaks command."""
    
    # Randomize X-Mailer to mimic common email clients
    x_mailers = [
        'Microsoft Outlook 16.0',
        'Microsoft Outlook 15.0',
        'Mozilla Thunderbird 78.14.0',
        'Mozilla Thunderbird 91.13.0',
        'Apple Mail (16.0)',
        'Apple Mail (14.0)',
        'Gmail - Android',
        'Outlook-Android/2.0',
        'Microsoft Outlook Express 6.00.2900.5512'
    ]
    
    # Additional legitimate headers for authenticity
    priorities = ['1 (Highest)', '3 (Normal)', '5 (Lowest)']
    
    selected_xmailer = random.choice(x_mailers)
    selected_priority = random.choice(priorities)
    
    cmd = [
        './swaks',
        '--auth',
        '--server', 'smtp.mailgun.org',
        '--au', sender_email,
        '--ap', sender_password,
        '--from', sender_email,
        '--header', f'From: {sender_display_name} <{sender_email}>',
        '--header', f'X-Mailer: {selected_xmailer}',
        '--header', f'X-Priority: {selected_priority}',
        '--header', 'MIME-Version: 1.0',
        '--header', 'Content-Type: text/plain; charset=UTF-8',
        '--to', recipient_email,
        '--h-Subject', subject,
        '--body', body
    ]
    
    try:
        print(f"Sending email to {recipient_email}...")
        print(f"Subject: {subject}")
        print(f"From: {sender_display_name} <{sender_email}>")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✓ Email sent successfully to {recipient_email}")
            return True
        else:
            print(f"✗ Failed to send email to {recipient_email}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout sending email to {recipient_email}")
        return False
    except Exception as e:
        print(f"✗ Error sending email to {recipient_email}: {e}")
        return False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Email sender with progressive scheduling')
    parser.add_argument('--setup-cron', action='store_true', help='Set up crontab for daily execution')
    parser.add_argument('--remove-cron', action='store_true', help='Remove crontab entry')
    parser.add_argument('--force-send', type=int, metavar='N', help='Force send N emails (ignores daily limits)')
    parser.add_argument('--status', action='store_true', help='Show current status and history')
    return parser.parse_args()

def main():
    """Main function to orchestrate the email sending process."""
    args = parse_arguments()
    script_dir = Path(__file__).parent
    
    # Handle command line flags
    if args.setup_cron:
        if setup_crontab():
            print("Crontab has been set up. The script will run daily at 10:00 AM.")
            print("It will automatically remove itself after 5 days.")
        return
    
    if args.remove_cron:
        remove_crontab()
        return
    
    # Load history
    history = load_history()
    
    if args.status:
        print("=== Email Sender Status ===")
        if history["start_date"]:
            start_date = datetime.strptime(history["start_date"], '%Y-%m-%d')
            current_date = datetime.now()
            day_number = (current_date - start_date).days + 1
            print(f"Campaign started: {history['start_date']}")
            print(f"Current day: {day_number}")
            print(f"Daily send history:")
            for date, count in sorted(history["daily_sends"].items()):
                print(f"  {date}: {count} emails sent")
        else:
            print("No campaign started yet.")
        return
    
    # Check if we should clean up crontab
    check_and_cleanup_crontab(history)
    
    # Load JSON files
    print("Loading configuration files...")
    
    send_data = load_json_file(script_dir / 'send.json')
    if not send_data:
        print("Error: Could not load send.json or file is empty.")
        sys.exit(1)
    
    messages_data = load_json_file(script_dir / 'messages.json')
    if not messages_data:
        print("Error: Could not load messages.json or file is empty.")
        sys.exit(1)
    
    receive_data = load_json_file(script_dir / 'receive.json')
    if not receive_data:
        print("Error: Could not load receive.json or file is empty.")
        sys.exit(1)
    
    # Validate data structures
    if not isinstance(send_data, list) or len(send_data) == 0:
        print("Error: send.json should contain a non-empty array of credential objects.")
        sys.exit(1)
    
    if not isinstance(messages_data, list) or len(messages_data) == 0:
        print("Error: messages.json should contain a non-empty array of message objects.")
        sys.exit(1)
    
    if not isinstance(receive_data, list) or len(receive_data) == 0:
        print("Error: receive.json should contain a non-empty array of recipient emails.")
        sys.exit(1)
    
    # Check if swaks is available
    if not os.path.exists('./swaks'):
        print("Error: swaks executable not found in current directory.")
        print("Please ensure swaks is available and executable.")
        sys.exit(1)
    
    print(f"Found {len(send_data)} credential sets")
    print(f"Found {len(messages_data)} message templates")
    print(f"Found {len(receive_data)} recipients")
    print()
    
    # Determine how many emails to send today
    if args.force_send:
        emails_to_send = args.force_send
        day_number = "FORCED"
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"Force sending {emails_to_send} emails")
    else:
        day_number, emails_to_send, today = get_current_day_info(history)
        print(f"Day {day_number}: Planning to send {emails_to_send} emails")
    
    if emails_to_send <= 0:
        print("No emails to send today (daily quota already met).")
        return
    
    # Limit emails to available recipients
    available_recipients = len(receive_data)
    if emails_to_send > available_recipients:
        print(f"Warning: Requested {emails_to_send} emails but only {available_recipients} recipients available.")
        emails_to_send = available_recipients
    
    # Randomly select recipients for today
    selected_recipients = random.sample(receive_data, emails_to_send)
    successful_sends = 0
    
    for i, recipient in enumerate(selected_recipients, 1):
        print(f"--- Processing recipient {i}/{emails_to_send} ---")
        
        # Randomly select credentials and message
        selected_creds = random.choice(send_data)
        selected_message = random.choice(messages_data)
        
        # Extract recipient email (handle both string and object formats)
        if isinstance(recipient, str):
            recipient_email = recipient
        elif isinstance(recipient, dict) and 'email' in recipient:
            recipient_email = recipient['email']
        else:
            print(f"✗ Invalid recipient format: {recipient}")
            continue
        
        # Extract sender info
        sender_email = selected_creds.get('email', '')
        sender_password = selected_creds.get('password', '')
        sender_display_name = selected_creds.get('display_name', sender_email)
        
        # Extract message info
        subject = selected_message.get('subject', 'Hello Great Meetings')
        body = selected_message.get('body', 'Hey there, just wanted to say thanks for the great meeting and business conversation the other day!')
        
        # Validate required fields
        if not sender_email or not sender_password:
            print(f"✗ Invalid credentials: missing email or password")
            continue
        
        # Send the email
        if send_email(sender_email, sender_password, sender_display_name, recipient_email, subject, body):
            successful_sends += 1
        
        # Add random delay before next email (except for the last one)
        if i < emails_to_send:
            delay = random.randint(30, 180)
            print(f"Waiting {delay} seconds before next email...")
            time.sleep(delay)
            print()
    
    # Update history with successful sends
    if not args.force_send and successful_sends > 0:
        update_history(history, today, successful_sends)
    
    print(f"--- Summary ---")
    print(f"Day {day_number}: Attempted to send {emails_to_send} emails")
    print(f"Successful sends: {successful_sends}")
    print(f"Failed sends: {emails_to_send - successful_sends}")
    
    if not args.force_send:
        print(f"History updated for {today}")
        remaining_recipients = len(receive_data) - sum(history["daily_sends"].values())
        print(f"Total recipients remaining: {remaining_recipients}")

if __name__ == "__main__":
    main()
