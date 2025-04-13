import subprocess
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI  # Import OpenAI library

# Load environment variables (like OPENAI_API_KEY)
load_dotenv()

# --- OpenAI Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"

# Initialize OpenAI client
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Other Configuration ---
# Add your bio or relevant context here to help the AI classify emails better
USER_BIO = """Replace this with your bio or other relevant context. 
For example: 'I am a software engineer interested in AI and startups.'"""

# Map classification categories to Apple Mail color *indexes*
LABEL_COLOR_MAP = {
    "alert": 2,  # Red Index
    "respond": 1,  # Orange Index
    "interesting": 6,  # Green Index
    "fyi": 4,  # Blue Index
    "idk": 5,  # Purple Index
    "delete": 7,  # Gray Index
}


def get_emails_from_apple_mail():
    """Fetch emails from the last 24 hours from Apple Mail using AppleScript"""
    applescript = """
    tell application "Mail"
        -- Check for new mail first
        check for new mail
        delay 1
        
        -- Calculate 24 hours ago
        tell (current date) to set oneDayAgo to it - (1 * days)
        
        -- Log the date we're using for debugging
        log "Getting emails since: " & (oneDayAgo as string)
        
        -- NEW APPROACH: Build a single delimited string instead of a list
        -- Using "<<<START>>>" and "<<<END>>>" markers for each email
        set completeResult to ""
        
        -- Try to find recent messages 
        try
            -- Get messages from the inbox from the last 24 hours
                set recentMessages to (messages of inbox whose date received comes after oneDayAgo)
            log "Found " & (count of recentMessages) & " messages in the last 24 hours"
            
            -- Process all messages found
            set messageCount to count of recentMessages

            if messageCount > 0 then
                repeat with i from 1 to messageCount -- Process all messages
                    try
                        set theMessage to item i of recentMessages
                        set msgID to id of theMessage
                        set msgSubject to subject of theMessage
                        set msgSender to sender of theMessage
                        set msgDate to (date received of theMessage) as string
                        set msgBody to content of theMessage
                        
                        log "Processing message: " & msgSubject
                        
                        -- Trim body if too long
                        if (count of characters of msgBody) > 500 then
                            set msgBody to (characters 1 through 500 of msgBody as string) & "..."
                        end if
                        
                        -- Escape any special characters in the content
                        set cleanSubject to my replaceText(msgSubject, "<<<", "[LT]")
                        set cleanSubject to my replaceText(cleanSubject, ">>>", "[GT]")
                        set cleanSender to my replaceText(msgSender, "<<<", "[LT]")
                        set cleanSender to my replaceText(cleanSender, ">>>", "[GT]")
                        set cleanBody to my replaceText(msgBody, "<<<", "[LT]")
                        set cleanBody to my replaceText(cleanBody, ">>>", "[GT]")
                        
                        -- Add to our result string with clear markers and tab separators
                        set completeResult to completeResult & "<<<START>>>" & msgID & "<<<TAB>>>" & cleanSubject & "<<<TAB>>>" & cleanSender & "<<<TAB>>>" & msgDate & "<<<TAB>>>" & cleanBody & "<<<END>>>"
                    on error errMsg
                        log "Error processing message: " & errMsg
                    end try
                end repeat
            end if
        on error errMsg
            log "Date filtering error: " & errMsg
            log "Falling back to getting most recent messages"
            
            -- Fallback to just getting the most recent 5 messages
            try
                set recentMessages to messages 1 through 5 of inbox
                repeat with msg in recentMessages
                    try
                        set msgID to id of msg
                        set msgSubject to subject of msg
                        set msgSender to sender of msg
                        set msgDate to (date received of msg) as string
                        set msgBody to content of msg
                        
                        -- Trim body if too long
                        if (count of characters of msgBody) > 500 then
                            set msgBody to (characters 1 through 500 of msgBody as string) & "..."
                        end if
                        
                        -- Escape any special characters in the content
                        set cleanSubject to my replaceText(msgSubject, "<<<", "[LT]")
                        set cleanSubject to my replaceText(cleanSubject, ">>>", "[GT]")
                        set cleanSender to my replaceText(msgSender, "<<<", "[LT]")
                        set cleanSender to my replaceText(cleanSender, ">>>", "[GT]")
                        set cleanBody to my replaceText(msgBody, "<<<", "[LT]")
                        set cleanBody to my replaceText(cleanBody, ">>>", "[GT]")
                        
                        -- Add to our result string with clear markers and tab separators
                        set completeResult to completeResult & "<<<START>>>" & msgID & "<<<TAB>>>" & cleanSubject & "<<<TAB>>>" & cleanSender & "<<<TAB>>>" & msgDate & "<<<TAB>>>" & cleanBody & "<<<END>>>"
                    on error errMsg
                        log "Error with fallback: " & errMsg
                    end try
                end repeat
            on error finalErr
                log "Failed all attempts: " & finalErr
            end try
        end try
        
        -- Return the complete result as a single string
        return completeResult
    end tell
    
    -- Helper function to replace text in a string
    on replaceText(sourceText, searchString, replacementString)
        set AppleScript's text item delimiters to searchString
        set textItems to every text item of sourceText
        set AppleScript's text item delimiters to replacementString
        set newText to textItems as string
        set AppleScript's text item delimiters to ""
        return newText
    end replaceText
    """

    try:
        print("Running AppleScript to fetch emails...")
        result = subprocess.run(
            ["osascript", "-e", applescript], capture_output=True, text=True, check=True
        )

        # Print log output for debugging
        if result.stderr:
            print("AppleScript log output:")
            for line in result.stderr.strip().split("\n"):
                if line.startswith('tell application "Mail"'):
                    continue
                elif "syntax error:" in line:
                    print(f"ERROR: {line}")
                else:
                    print(f"LOG: {line}")

        # Process the output using our new approach with markers
        raw_output = result.stdout.strip()
        print(f"Raw output length: {len(raw_output)} characters")

        # Split the output by our markers
        emails = []
        if "<<<START>>>" in raw_output:
            email_parts = raw_output.split("<<<START>>>")
            # Skip the first part (it's empty)
            for part in email_parts[1:]:
                if "<<<END>>>" in part:
                    # Extract the content between START and END
                    email_data = part.split("<<<END>>>")[0]
                    # Split the data by TAB markers
                    fields = email_data.split("<<<TAB>>>")

                    if len(fields) == 5:
                        mail_id_str, subject, sender, date_str, body = fields

                        # Restore any escaped markers
                        subject = subject.replace("[LT]", "<").replace("[GT]", ">")
                        sender = sender.replace("[LT]", "<").replace("[GT]", ">")
                        body = body.replace("[LT]", "<").replace("[GT]", ">")

                        # Clean up the text
                        subject = subject.strip()
                        sender = sender.strip()
                        body = body.strip()
                        date_str = date_str.strip()

                        # Parse the ID as an integer
                        try:
                            mail_id = int(mail_id_str.strip())

                            # Add the email to our list
                            emails.append(
                                {
                                    "id": mail_id,
                                    "subject": subject,
                                    "sender": sender,
                                    "date": date_str,
                                    "body": body,
                                }
                            )

                            print(f"Successfully parsed email: {subject}")
                        except ValueError:
                            print(f"Warning: Could not parse email ID: {mail_id_str}")
                    else:
                        print(
                            f"Warning: Email data has wrong number of fields: {len(fields)}"
                        )

        print(f"Successfully parsed {len(emails)} emails from AppleScript output")
        return emails

    except subprocess.CalledProcessError as e:
        print(f"Error fetching emails from Apple Mail: {e}")
        print(f"Error output: {e.stderr}")
        return []


def classify_email(email):
    """Use OpenAI API to classify a single email according to personalized categories."""

    system_prompt = """You are an expert email classification assistant for a busy founder. 
Your task is to analyze the provided email and classify it according to the user's specific preferences."""

    user_prompt = f"""Please classify this email into exactly ONE of these categories, listed in rough order of priority:

alert: Emails containing time-sensitive information or requiring action *other than* a direct reply. This includes things like 2FA codes, flight updates, confirmation links, password resets, or urgent alerts that need attention but not a written response back to the sender. Assign this for truly urgent items.

respond: Emails that require a response from me. This includes personalized messages from real people, important questions, or time-sensitive matters that I should reply to.

interesting: Content that might be intellectually stimulating or worth reading later. This could be newsletters from interesting people, thought pieces, or content that aligns with my interests.

fyi: Informational emails that I should be aware of but don't need immediate action. This includes updates, notices, and general information. Like emails from my bank, or my credit card company. Standard password resets might fit here if not immediately needed.

delete: Spam, marketing, or low-value emails that are safe to ignore or delete. This includes mass-marketing, promotional emails, and non-personalized outreach.

idk: When you're not sure which category it belongs in or it doesn't clearly fit elsewhere.

Some context about me:
{USER_BIO}

Some context on my preferences:
- Prioritize `alert` for things needing immediate awareness/action (invoices, 2FA, time-sensitive links, travel updates, etc).
- Prioritize `respond` for direct communication from real people.
- Use `interesting` for newsletters or content I might want to read later.
- Use `fyi` for general updates (bank statements, product updates).
- Use `delete` for clear spam/marketing.
- When in doubt, err on the side of caution with 'idk'

From: {email["sender"]}
Subject: {email["subject"]}
Content: {email["body"]}
Date Sent: {email["date"]}

Provide your classification and a brief explanation why in JSON format:
{{"classification": "alert/respond/interesting/fyi/delete/idk", "reason": "your explanation here"}}
"""

    valid_labels = {"alert", "respond", "interesting", "fyi", "delete", "idk"}

    try:
        # Call OpenAI API
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=300,
            response_format={"type": "json_object"},
        )

        content = completion.choices[0].message.content

        # Parse the JSON response from OpenAI
        try:
            classification_data = json.loads(content)

            # Extract the classification and reason
            classification = classification_data.get("classification", "").strip()
            reason = classification_data.get("reason", "").strip()

            # Validate the classification
            if classification in valid_labels:
                return {"label": classification, "reason": reason}
            else:
                print(
                    f"Invalid classification '{classification}' from OpenAI for email ID {email['id']}. Falling back to 'idk'."
                )
                return {
                    "label": "idk",
                    "reason": f"Classification '{classification}' was invalid, using fallback.",
                }

        except json.JSONDecodeError as e:
            print(
                f"JSON decode error for email ID {email['id']} from OpenAI response: {e}"
            )
            print(f"OpenAI raw response: {content}")
            return {
                "label": "idk",
                "reason": "Failed to parse JSON response from OpenAI.",
            }

    except Exception as e:
        print(f"Error calling OpenAI API for email ID {email['id']}: {e}")
        return None  # Indicate failure


def apply_mail_label(email_id, label, subject):
    """Apply a color label to an email using AppleScript."""

    # Get the appropriate color INDEX from our mapping (default to 0 - None)
    color_index = LABEL_COLOR_MAP.get(label, 0)

    # Corrected AppleScript using 'whose id is' syntax
    applescript = f"""
    tell application "Mail"
        set targetID to {email_id}
        set theColorIndex to {color_index} -- Use the integer directly
        set targetMessage to null

        try
            -- Try getting the message from inbox using 'whose' clause
            set matchingMessagesInbox to (messages of inbox whose id is targetID)
            if (count of matchingMessagesInbox) > 0 then
                set targetMessage to item 1 of matchingMessagesInbox
            end if
        on error errMsgInbox
            -- Log or ignore error searching inbox
            log "Error searching inbox by ID " & targetID & ": " & errMsgInbox
        end try

        -- If not found in inbox, try sent mailbox
        if targetMessage is null then
            try
                set matchingMessagesSent to (messages of sent mailbox whose id is targetID)
                if (count of matchingMessagesSent) > 0 then
                    set targetMessage to item 1 of matchingMessagesSent
                end if
            on error errMsgSent
                -- Log or ignore error searching sent mailbox
                 log "Error searching sent mailbox by ID " & targetID & ": " & errMsgSent
            end try
        end if

        -- Apply label if found
        if targetMessage is not null then
            try
                set flag index of targetMessage to theColorIndex
                return "Success: Label applied (found by ID)."
            on error errMsgSetFlag
                return "Error - Flag Set Failed: " & errMsgSetFlag
            end try
        else
            log "Message ID " & targetID & " not found in inbox or sent mailbox using 'whose id'."
            return "Error - Message Not Found (using ID)"
        end if
    end tell
    """

    try:
        result = subprocess.run(
            ["osascript", "-e", applescript], capture_output=True, text=True, check=True
        )
        print(f"Applied '{label}' label to email ID {email_id} (Subject: '{subject}')")
        if result.stdout:
            print(f"Result: {result.stdout.strip()}")
        if result.stderr:
            print(f"Error: {result.stderr.strip()}")

    except subprocess.CalledProcessError as e:
        print(f"Error applying '{label}' label to email ID {email_id}: {e}")
        print(f"Stderr: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def main():
    print(f"=== Email Classification Agent Started at {datetime.now()} ===")

    # 1. Fetch recent emails from Apple Mail
    print("Fetching recent emails from Apple Mail...")
    emails = get_emails_from_apple_mail()
    print(f"Found {len(emails)} emails to process")

    if not emails:
        print("No emails to process. Exiting.")
        return

    # 2. Process each email individually
    print("\nProcessing emails one by one...")
    processed_count = 0
    for email in emails:
        print(f"\n--- Processing Email ID: {email['id']} ---")
        print(f"From: {email['sender']}")
        print(f"Subject: {email['subject']}")
        print(f"Date: {email['date']}")

        # 2a. Classify the email
        classification = classify_email(email)

        if classification:
            print(f"Classification: {classification['label']}")
            print(f"Reason: {classification['reason']}")

            # 2b. Apply the label in Mail
            apply_mail_label(email["id"], classification["label"], email["subject"])
            processed_count += 1
        else:
            print(
                f"Skipping label application for email ID {email['id']} due to classification error."
            )

    print(f"\n=== Email Classification Completed at {datetime.now()} ===")
    print(
        f"Successfully processed and labeled {processed_count} out of {len(emails)} fetched emails."
    )


if __name__ == "__main__":
    main()
