# MercuryRising
Gradually raise the temperature of phishing campaign sender emails/domains!

<p align="center"><img src="https://github.com/Luct0r/assets/blob/master/freddy_mercury.png" width="300"/></p>

## Overview
A simple python script that randomly selects credentials and messages to send emails with random delays and checks previous sending history to gradually ramp up activity using swaks.

## Setup
1. Setup a generic GCP or AWS server to run this script from, and make sure the sending domain(s) have proper SPF, DKIM, and DMARC.

2. **Install swaks**
Go to https://github.com/jetmore/swaks and find the recent release.

   ```bash
   apt install perl -y
   curl -O https://jetmore.org/john/code/swaks/files/swaks-20240103.0/swaks
   chmod 755 ./swaks
   ```

3. **Configure your JSON files**:

   - **send.json**: Contains sender credentials
     ```json
     [
       {
         "email": "sender@domain.com",
         "password": "your_password",
         "display_name": "Your Name"
       }
     ]
     ```

   - **messages.json**: Contains message templates (already configured, but feel free to can add more)
   
   - **receive.json**: Contains recipient email addresses
     ```json
     [
       "recipient1@example.com",
       "recipient2@example.com"
     ]
     ```

## Usage

### Basic Usage (Manual)
This can be ran manually to either test email delivery and/or to warm domains:

```bash
python3 email_sender.py
```

### Progressive Campaign (Recommended)
For true domain warming, use the automated progressive campaign that gradually increases email volume (preferably about a week prior to the real campaign):

```bash
# Set up automatic daily execution at 10:00 AM with progressive sending
python3 email_sender.py --setup-cron

# Check campaign status and history
python3 email_sender.py --status

# Remove crontab entry manually (auto-removes after 5 days)
python3 email_sender.py --remove-cron

# Force send specific number of emails (ignores daily limits)
python3 email_sender.py --force-send 3
```

The progressive campaign automatically:
- **Day 1**: Sends 1 email
- **Day 2**: Sends 2 emails  
- **Day 3**: Sends 3 emails
- **Day 4**: Sends 4 emails
- **Day 5**: Sends 5 emails
- **After Day 5**: Automatically removes crontab entry

## Features

### Core Functionality
- Randomly selects sender credentials from `send.json`
- Randomly selects message templates from `messages.json`
- Random delay between 30-180 seconds between emails
- Comprehensive error handling and logging
- Progress tracking and summary reporting

### Progressive Campaign Management
- Automatic daily execution via crontab
- History tracking in `history.json` file
- Prevents duplicate sends on the same day
- Progressive volume increase (1, 2, 3, 4, 5 emails per day)
- Auto-cleanup after 5-day campaign
- Command line flags for manual control and status checking

## Requirements

- Python 3.6+
- swaks email tool
- Valid SMTP credentials

## Security Note

Keep your `send.json` file secure and never commit it to version control with real credentials.
