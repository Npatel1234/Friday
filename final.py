import pdfplumber
import requests
from bs4 import BeautifulSoup
import os
from transformers import pipeline
import json
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import time
import pickle
import pathlib
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ✅ LM Studio API Configuration
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# ✅ Initialize Summarizer
summarizer = pipeline("summarization")

# ✅ Memory Configuration
CONVERSATION_FILE = "conversation_history.json"
PDF_CONTENT = {}  # Store PDF content in memory

# ✅ WhatsApp Configuration
class WhatsAppBot:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None
        
        # Brave browser paths
        self.brave_exe = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
        self.user_data_dir = os.path.expanduser('~') + "\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data"

    def start(self):
        try:
            self.playwright = sync_playwright().start()
            
            # Launch browser with optimized settings
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                executable_path=self.brave_exe,
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--start-maximized',
                    '--no-default-browser-check',
                    '--no-first-run',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            # Use first page or create new one
            if len(self.browser.pages) > 0:
                self.page = self.browser.pages[0]
            else:
                self.page = self.browser.new_page()
            
            # Navigate to WhatsApp Web with reduced timeout
            self.page.goto("https://web.whatsapp.com", wait_until='domcontentloaded')
            
            # Quick check for WhatsApp load
            try:
                self.page.wait_for_selector('[data-testid="chat-list"]', timeout=15000)
                print("WhatsApp loaded!")
                return True
            except:
                print("WhatsApp loading...")
                return True  # Continue anyway as the page might still be loading
            
        except Exception as e:
            print(f"Error starting browser: {e}")
            return False

    def send_message(self, contact_name, message):
        try:
            # Quick status check
            if not self.page:
                if not self.start():
                    return "Failed to start browser"

            # Search for contact with reduced timeout
            search_box = self.page.wait_for_selector("div[contenteditable='true']", timeout=5000)
            if not search_box:
                search_box = self.page.wait_for_selector('[data-testid="chat-list"]', timeout=5000)
            
            if search_box:
                search_box.click()
                search_box.fill(contact_name)
                self.page.keyboard.press("Enter")
                
                time.sleep(1)  # Reduced wait time

                # Find message box with optimized selectors
                message_box = None
                for selector in ["div[title='Type a message']", "footer div[contenteditable='true']"]:
                    try:
                        message_box = self.page.wait_for_selector(selector, timeout=3000)
                        if message_box:
                            break
                    except:
                        continue

                if message_box:
                    message_box.click()
                    message_box.fill(message)
                    self.page.keyboard.press("Enter")
                    return "Message sent successfully!"
                else:
                    return "Could not find message box"
            else:
                return "Could not find search box"

        except Exception as e:
            return f"Error: {str(e)}"

    def close(self):
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass

# ✅ Email Configuration
class EmailBot:
    def __init__(self):
        # Replace with your Gmail credentials
        self.email = "neelspatel3677@gmail.com"
        self.password = "tcsw cbtv dwyo geof"  # Use App Password from Google Account
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.imap_server = "imap.gmail.com"
        
        # Define important criteria
        self.important_senders = [
            'boss@company.com',
            'important@company.com',
            'npatel3032@gmail.com',  # Add your important contacts
            'urgent@company.com',
            'noreply@linkedin.com',
            'notifications@github.com',
            'name21ecs@student.mes.ac.in'
        ]
        
        self.important_keywords = [
            'urgent',
            'important',
            'action required',
            'deadline',
            'meeting',
            'interview',
            'offer',
            'approved',
            'review',
            'critical',
            'alert',
            'priority'
        ]

    def is_email_important(self, email_message):
        """Check if an email is important based on multiple criteria"""
        try:
            # Get email details
            subject = email_message['subject'].lower() if email_message['subject'] else ''
            sender = email_message['from'].lower() if email_message['from'] else ''
            
            # Check sender
            if any(important_sender.lower() in sender for important_sender in self.important_senders):
                return True
                
            # Check subject for important keywords
            if any(keyword in subject for keyword in self.important_keywords):
                return True
            
            # Check if email is marked as priority
            if email_message['x-priority'] and email_message['x-priority'] in ['1', '2']:
                return True
                
            # Check if the email is a reply to your email
            if 'in-reply-to' in email_message and email_message['in-reply-to']:
                return True
                
            # Check if you're mentioned in CC
            if email_message['cc'] and self.email.lower() in email_message['cc'].lower():
                return True
                
            return False
            
        except Exception as e:
            print(f"Error checking email importance: {e}")
            return False

    def send_email(self, to_email, subject, body):
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            return "Email sent successfully!"
        except Exception as e:
            return f"Error sending email: {str(e)}"

    def check_new_emails(self, minutes=30):
        try:
            imap = imaplib.IMAP4_SSL(self.imap_server)
            imap.login(self.email, self.password)
            imap.select("INBOX")

            # Calculate time threshold
            time_threshold = (datetime.now() - timedelta(minutes=minutes)).strftime("%d-%b-%Y")
            
            # Search for recent emails
            _, messages = imap.search(None, f'(SINCE "{time_threshold}")')
            
            important_emails = []
            for num in messages[0].split():
                _, msg = imap.fetch(num, "(RFC822)")
                email_body = msg[0][1]
                email_message = email.message_from_bytes(email_body)
                
                if self.is_email_important(email_message):
                    # Get email body preview
                    body_preview = ""
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                body_preview = part.get_payload(decode=True).decode()[:100] + "..."
                                break
                    else:
                        body_preview = email_message.get_payload(decode=True).decode()[:100] + "..."

                    important_emails.append({
                        'from': email_message['from'],
                        'subject': email_message['subject'],
                        'date': email_message['date'],
                        'preview': body_preview
                    })
            
            imap.close()
            imap.logout()
            
            if important_emails:
                return "Found {} important emails:\n\n".format(len(important_emails)) + \
                       "\n\n".join([
                           f"From: {e['from']}\n"
                           f"Subject: {e['subject']}\n"
                           f"Date: {e['date']}\n"
                           f"Preview: {e['preview']}"
                           for e in important_emails
                       ])
            return "No important new emails."
            
        except Exception as e:
            return f"Error checking emails: {str(e)}"

# ✅ Memory Functions
def load_conversation_history():
    if os.path.exists(CONVERSATION_FILE):
        try:
            with open(CONVERSATION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_conversation_history(history):
    with open(CONVERSATION_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2, default=str)

conversation_memory = []
conversation_history = load_conversation_history()
MEMORY_LIMIT = 5

def save_to_history(user_input, assistant_response):
    conversation_history.append({
        'user': user_input,
        'assistant': assistant_response,
        'timestamp': datetime.now().isoformat()
    })
    save_conversation_history(conversation_history)

# ✅ PDF Functions
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def query_llama2(prompt):
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": False
    }
    
    try:
        response = requests.post(LM_STUDIO_API_URL, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            return f"❌ API Error: {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"❌ Request Failed: {str(e)}"

def pdf_qa(whatsapp_bot=None, contact_name=None):
    print("Would you like to process a single PDF or multiple PDFs? (Type 'single' or 'multiple')")
    choice = input("You: ").strip().lower()
    
    if choice == "single":
        pdf_path = input("Enter the path of the PDF file: ").strip()
        pdf_paths = [pdf_path]
    elif choice == "multiple":
        pdf_paths = input("Enter paths of multiple PDFs separated by commas: ").strip().split(",")
        pdf_paths = [path.strip() for path in pdf_paths]
    else:
        print("Invalid choice. Returning to main conversation.")
        return

    print(f"Processing {choice} PDF(s)...")
    
    for path in pdf_paths:
        if os.path.exists(path):
            content = extract_text_from_pdf(path)
            if content:
                PDF_CONTENT[path] = content
                print(f"✅ Successfully processed: {path}")
            else:
                print(f"❌ No content extracted from: {path}")
        else:
            print(f"❌ File not found: {path}")
    
    while True:
        question = input("Ask your question about the PDF(s) or type 'exit' to return: ").strip()
        if question.lower() in ["exit", "quit"]:
            print("Returning to main conversation.")
            break
        
        context = "\n".join(PDF_CONTENT.values())
        prompt = f"PDF Content: {context[:2000]}\nUser Question: {question}\nAnswer:"
        
        answer = query_llama2(prompt)
        print(f"💡 Answer: {answer}")
        save_to_history(question, answer)

        # Send answer through WhatsApp if bot is available
        if whatsapp_bot and contact_name:
            whatsapp_bot.send_message(contact_name, f"Q: {question}\nA: {answer}")

# ✅ Update main conversation handler
def handle_conversation(user_input, whatsapp_bot=None, email_bot=None):
    if "whatsapp" in user_input.lower():
        if not whatsapp_bot:
            return "WhatsApp bot is not initialized!"
        
        try:
            _, command = user_input.split("whatsapp", 1)
            contact, message = command.strip().split(":", 1)
            result = whatsapp_bot.send_message(contact.strip(), message.strip())
            save_to_history(user_input, result)
            return result
        except:
            return "Please use format: whatsapp contact_name: message"
    
    elif "meeting" in user_input.lower():
        if not email_bot:
            return "Email bot is not initialized!"
        
        try:
            _, command = user_input.split("meeting", 1)
            contact, message = command.strip().split(":", 1)
            result = email_bot.send_email(contact.strip(), "Meeting Reminder", message.strip())
            
            # Send a copy to yourself
            if result == "Email sent successfully!":
                copy_subject = f"[COPY] Meeting Reminder sent to {contact.strip()}"
                copy_body = f"This is a copy of the meeting reminder sent to {contact.strip()}:\n\n{message.strip()}"
                email_bot.send_email(email_bot.email, copy_subject, copy_body)
                return f"Meeting reminder sent to {contact.strip()} and a copy was sent to your email!"
            return result
        except:
            return "Please use format: meeting email@example.com: Your meeting message"

    elif "email" in user_input.lower():
        if not email_bot:
            return "Email bot is not initialized!"
        
        if "check" in user_input.lower():
            # Check for new important emails
            minutes = 30  # Default to last 30 minutes
            try:
                # Try to extract custom time period
                time_str = user_input.lower().split("check emails", 1)[1].strip()
                if "hour" in time_str:
                    minutes = 60 * int(time_str.split("hour")[0].strip())
                elif "minute" in time_str:
                    minutes = int(time_str.split("minute")[0].strip())
            except:
                pass
            
            result = email_bot.check_new_emails(minutes)
            save_to_history(user_input, result)
            return result
        
        try:
            # Format: email to:recipient@email.com subject:Email Subject body:Email Body
            command = user_input.split("email", 1)[1].strip()
            to_email = command.split("subject:")[0].replace("to:", "").strip()
            subject = command.split("subject:")[1].split("body:")[0].strip()
            body = command.split("body:")[1].strip()
            
            result = email_bot.send_email(to_email, subject, body)
            save_to_history(user_input, result)
            return result
        except:
            return "Please use format: email to:recipient@email.com subject:Email Subject body:Email Body"
    
    # Handle other conversation types...
    return query_llama2(user_input)

def main():
    print("Welcome to AI Assistant with WhatsApp and Email Integration!")
    print("Commands:")
    print("1. 'pdf' - Process and query PDFs")
    print("2. 'whatsapp contact_name: message' - Send WhatsApp message")
    print("3. 'email to:email@example.com subject:Subject body:Message' - Send email")
    print("4. 'check emails [time period]' - Check for important emails")
    print("5. 'meeting email@example.com: Meeting details' - Send meeting reminder")
    print("6. 'exit' or 'quit' - Exit the program")

    whatsapp_bot = WhatsAppBot()
    email_bot = EmailBot()
    
    try:
        whatsapp_bot.start()
        
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            
            response = handle_conversation(user_input, whatsapp_bot, email_bot)
            print(f"Assistant: {response}")
    
    finally:
        whatsapp_bot.close()

if __name__ == "__main__":
    main() 