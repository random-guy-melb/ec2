from __future__ import annotations
from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime, timedelta
from tqdm import tqdm
import traceback

import requests
import pandas as pd
import json
import time
import re
import os
import random


from common.prompts import sys_prompts_extraction
from common.models.model import load_model

# Constants
MAX_RETRIES = 5
INITIAL_BACKOFF = 1
RATE_LIMIT_STATUS = 429
DEFAULT_LIMIT = 100
MAX_MESSAGES_PER_THREAD = 1000
MAX_CONVERSATION_LENGTH = 30000  # Character limit for LLM processing

# Base directory for saving data
BASE_OUTPUT_DIR = "./csv_data"
# Log file path
LOG_FILE_PATH = "./csv_data/slack_extraction_log.json"

# Slack API endpoints
USERS_LIST_URL = 'https://slack.com/api/users.list'
CHANNELS_LIST_URL = 'https://slack.com/api/conversations.list'
USERGROUPS_LIST_URL = 'https://slack.com/api/usergroups.list'
CONVERSATIONS_HISTORY_URL = 'https://slack.com/api/conversations.history'
CONVERSATIONS_REPLIES_URL = 'https://slack.com/api/conversations.replies'


def clean_text(text: str | None) -> str:
    """Clean text by removing control characters and normalizing whitespace."""
    if not text:
        return ""
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.strip()


def remove_hyperlink(text: str) -> str:
    """Remove Slack hyperlinks from text."""
    return re.sub("<https:.*?>", " ", text)


def replace_name_tags(text: str) -> str:
    """Replace user mention tags with generic @user."""
    return re.sub(r"<@([A-Z0-9]+)>", "@user", text).strip()


def remove_misc_tags(text: str) -> str:
    """Remove miscellaneous Slack tags."""
    return re.sub("<!.*?>", " ", text)


def unix_timestamp(dt: datetime) -> int:
    """Convert datetime to Unix timestamp."""
    return int(dt.timestamp())


def format_date_for_filename(date_input: str | datetime) -> str:
    """Format a date for filename convention."""
    if isinstance(date_input, str):
        dt = datetime.strptime(date_input, "%Y-%m-%d")
    else:
        dt = date_input
    return dt.strftime("%Y%m%d")


def make_request_with_backoff(session: requests.Session,
                              url: str,
                              params: Dict[str, Any],
                              max_retries: int = MAX_RETRIES,
                              initial_backoff: float = INITIAL_BACKOFF) -> Optional[Dict]:
    """Make HTTP request with exponential backoff for rate limiting."""
    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == RATE_LIMIT_STATUS:
                if attempt < max_retries - 1:
                    backoff_time = initial_backoff * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Rate limited. Retrying in {backoff_time:.2f} seconds...")
                    time.sleep(backoff_time)
                else:
                    print("Max retries reached. Skipping this request.")
                    return None
            else:
                print(f"HTTP error: {e}")
                return None
        except requests.RequestException as e:
            print(f"Request Error: {e}")
            return None


def fetch_workspace_data(session: requests.Session) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """Fetch all users, channels, and user groups in the workspace."""
    print("Fetching workspace data...")

    # Fetch users
    users = {}
    cursor = None
    print("  Fetching users...")

    while True:
        params = {'limit': 200}
        if cursor:
            params['cursor'] = cursor

        data = make_request_with_backoff(session, USERS_LIST_URL, params)

        if data and data['ok']:
            for member in data['members']:
                try:
                    users[member['id']] = member.get('real_name', member['name'])
                except:
                    users[member['id']] = member.get('profile', {}).get('real_name', 'Unknown')

            if data.get('response_metadata', {}).get('next_cursor'):
                cursor = data['response_metadata']['next_cursor']
            else:
                break
        else:
            print("  Error fetching users. Some user IDs may not be resolved.")
            break

    print(f"  Found {len(users)} users")

    # Fetch channels
    channels = {}
    cursor = None
    print("  Fetching channels...")

    while True:
        params = {'limit': 200, 'types': 'public_channel,private_channel'}
        if cursor:
            params['cursor'] = cursor

        data = make_request_with_backoff(session, CHANNELS_LIST_URL, params)

        if data and data['ok']:
            for channel in data['channels']:
                channels[channel['id']] = channel['name']

            if data.get('response_metadata', {}).get('next_cursor'):
                cursor = data['response_metadata']['next_cursor']
            else:
                break
        else:
            print("  Error fetching channels. Some channel IDs may not be resolved.")
            break

    print(f"  Found {len(channels)} channels")

    # Fetch user groups
    usergroups = {}
    print("  Fetching user groups...")

    data = make_request_with_backoff(session, USERGROUPS_LIST_URL, {})
    if data and data['ok']:
        for group in data['usergroups']:
            usergroups[group['id']] = group['handle']
        print(f"  Found {len(usergroups)} user groups")
    else:
        print("  Error fetching user groups. Some user group IDs may not be resolved.")

    return users, channels, usergroups


def resolve_names(text: str, users: Dict[str, str], channels: Dict[str, str], usergroups: Dict[str, str]) -> str:
    """Replace user, channel, and user group IDs with their respective names."""

    def replace_id(match):
        full_match = match.group(0)

        if match.group(1) == '@':
            user_id = match.group(2)
            return f"@{users.get(user_id, user_id)}"
        elif match.group(1) == '#':
            channel_id = match.group(2)
            return f"#{channels.get(channel_id, channel_id)}"
        elif match.group(1) == '!':
            group_id = match.group(2)
            if '^' in group_id:
                id = group_id.split("^")[1].strip()
                return f"@{usergroups.get(id, id)}"
            return full_match
        else:
            return full_match

    pattern = r'<([@#!])(U[A-Z0-9]+|C[A-Z0-9]+|subteam\^S[0-9A-Z]+)>'
    return re.sub(pattern, replace_id, text)


def fetch_thread_replies(session: requests.Session, channel_id: str, thread_ts: str) -> List[Dict]:
    """Fetch all replies in a thread."""
    replies_params = {
        "channel": channel_id,
        "ts": thread_ts,
        "limit": 100
    }

    all_replies = []
    cursor = None

    while len(all_replies) < MAX_MESSAGES_PER_THREAD:
        if cursor:
            replies_params['cursor'] = cursor

        data = make_request_with_backoff(session, CONVERSATIONS_REPLIES_URL, replies_params)

        if data and data["ok"]:
            messages = data["messages"][1:]  # Skip the parent message
            all_replies.extend(messages)

            if data.get('has_more') and data.get('response_metadata', {}).get('next_cursor'):
                cursor = data['response_metadata']['next_cursor']
            else:
                break
        else:
            break

    return all_replies[:MAX_MESSAGES_PER_THREAD]


def format_thread_data(thread: List[Dict],
                       users: Dict[str, str],
                       channels: Dict[str, str],
                       usergroups: Dict[str, str]) -> Dict[str, Any]:
    """Format a thread into a structured dictionary."""
    parent = thread[0]

    # Get user info
    user_id = parent.get('user', 'Unknown')
    user_name = users.get(user_id, user_id)

    # Clean and resolve names in text
    clean_thread_text = clean_text(resolve_names(parent.get('text', ''), users, channels, usergroups))

    # Format timestamp
    date = datetime.fromtimestamp(float(parent['ts']))
    date_str = date.strftime("%Y-%m-%d")
    datetime_str = date.strftime("%Y-%m-%d %H:%M:%S")

    # Build thread text
    thread_text = f"{user_name} | {datetime_str}: {clean_thread_text}"

    # Process replies
    replies_array = []
    if len(thread) > 1:
        for reply in thread[1:]:
            reply_user_id = reply.get('user', 'Unknown')
            reply_user_name = users.get(reply_user_id, reply_user_id)

            clean_reply = clean_text(resolve_names(reply.get('text', ''), users, channels, usergroups))
            reply_date = datetime.fromtimestamp(float(reply['ts']))

            replies_array.append(
                f"{reply_user_name} | {reply_date.strftime('%Y-%m-%d %H:%M:%S')}: {clean_reply}"
            )

    full_conversation = thread_text
    if replies_array:
        full_conversation += "\n\n" + "\n\n".join(replies_array)

    return {
        'conversation': full_conversation,
        'date': date_str,
        'timestamp': parent['ts'],
        'thread_ts': parent.get('thread_ts', parent['ts']),
        'user': user_name,
        'channel_id': parent.get('channel', ''),
        'reply_count': len(replies_array),
        'participants': len(set([user_id] + [r.get('user', '') for r in thread[1:]]))
    }


def extract_slack_threads(token: str,
                          channel_id: str,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          max_threads: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Extract Slack threads from a channel within a date range."""
    # Initialize session
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    session = requests.Session()
    session.headers.update(headers)

    # Fetch workspace data
    users, channels, usergroups = fetch_workspace_data(session)

    # Convert dates to timestamps
    oldest = unix_timestamp(datetime.strptime(start_date, "%Y-%m-%d")) if start_date else None
    latest = unix_timestamp(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)) if end_date else None

    # Initial parameters
    params = {
        "channel": channel_id,
        "limit": DEFAULT_LIMIT
    }
    if oldest:
        params["oldest"] = oldest
    if latest:
        params["latest"] = latest

    print(f"\nExtracting threads from channel {channels.get(channel_id, channel_id)}")
    if start_date and end_date:
        print(f"Date range: {start_date} to {end_date}")

    all_threads = []
    total_messages = 0

    # Progress tracking
    pbar = tqdm(desc="Fetching messages", unit="messages")

    while True:
        data = make_request_with_backoff(session, CONVERSATIONS_HISTORY_URL, params)

        if data and data["ok"]:
            messages = data["messages"]
            total_messages += len(messages)
            pbar.update(len(messages))

            for message in messages:
                # Skip bot messages
                user = message.get("user", message.get("subtype", ""))
                if user != "USLACKBOT" and "bot" not in user.lower():
                    thread = [message]

                    # Fetch replies if it's a thread
                    if message.get("thread_ts") and message.get("reply_count", 0) > 0:
                        replies = fetch_thread_replies(session, channel_id, message["ts"])
                        if replies:
                            thread.extend(replies)

                    all_threads.append(thread)

                    if max_threads and len(all_threads) >= max_threads:
                        break

            if max_threads and len(all_threads) >= max_threads:
                break

            if data.get("has_more"):
                params["cursor"] = data.get("response_metadata", {}).get("next_cursor")
                if not params["cursor"]:
                    # Fallback to timestamp-based pagination
                    params["latest"] = messages[-1]['ts']
            else:
                break
        else:
            print("Error fetching messages. Exiting.")
            break

    pbar.close()

    print(f"\nFound {len(all_threads)} threads from {total_messages} messages")

    # Convert threads to DataFrame
    thread_data = []
    for thread in tqdm(all_threads, desc="Processing threads"):
        thread_data.append(format_thread_data(thread, users, channels, usergroups))

    df = pd.DataFrame(thread_data)

    # Stats
    stats = {
        'total_threads': len(all_threads),
        'total_messages': total_messages,
        'total_replies': sum(t['reply_count'] for t in thread_data),
        'unique_participants': len(set(m.get('user', '') for thread in all_threads for m in thread)),
        'channel_name': channels.get(channel_id, channel_id)
    }

    return df, stats


def process_with_llm(raw_file_path: str,
                     summary_file_path: str,
                     llm_model: str = "SelfHealing-gpt-40",
                     api_version: str = "2024-02-01") -> Dict[str, Any]:
    """Process extracted Slack conversations with LLM to extract issues and metadata."""
    print(f"\nProcessing conversations with LLM...")
    print(f"  Input: {raw_file_path}")
    print(f"  Output: {summary_file_path}")

    llm = load_model('openaichat')

    processed_count = 0
    skipped_count = 0
    error_count = 0

    try:
        # Read the raw CSV file
        df = pd.read_csv(raw_file_path, encoding='utf-8-sig')
        total_rows = len(df)

        # Prepare summary data
        summary_data = []

        # Process each conversation
        for idx, row in tqdm(df.iterrows(), total=total_rows, desc="Processing with LLM"):
            try:
                conv = remove_hyperlink(row['conversation'])

                if len(conv) > MAX_CONVERSATION_LENGTH:
                    skipped_count += 1
                    continue

                # Extract issues using LLM
                llm.SYS_PROMPT = sys_prompts_extraction.slack_oai_issue_extract
                issue_extraction = llm.generate_response(
                    input_data=conv,
                    model=llm_model,
                    api_version=api_version,
                    max_tokens=10000
                )

                if "NA" in issue_extraction:
                    skipped_count += 1
                    continue

                # Extract metadata using LLM
                llm.SYS_PROMPT = sys_prompts_extraction.slack_oai_metadata_extraction
                metadata = llm.generate_response(
                    input_data=conv,
                    model=llm_model,
                    api_version=api_version,
                    max_tokens=10000
                )

                category, context, groupID, tag = [
                    text for text in metadata.split("\n") if text.strip()
                ]
                issue, resolution = issue_extraction.split("==========================")
                issue, resolution = issue.strip(), resolution.strip()
                resolution_summary = f"{category}\n{issue}\n{resolution}\n{context}\n{groupID}\n{tag}"

                summary_data.append({
                    'Conversation': conv,
                    'Summary': resolution_summary,
                    'High Level Cause': category,
                    'Short Description': f"{issue}\n{context}",
                    'Resolution Type': resolution,
                    'Assignment Group': groupID,
                    'Tag': tag,
                    'Resolved': 'yes',
                    'Date': row['date'],
                    'Ts': row['timestamp']
                })

                processed_count += 1
                print(resolution_summary)
                print("\n")

            except Exception as e:
                error_count += 1
                if idx < 5:  # Only print first few errors
                    print(f"  Error processing row {idx}: {str(e)}")

        # Save summary data
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_csv(summary_file_path, index=False, encoding='utf-8-sig')
            print(f"\nSaved {len(summary_data)} processed conversations to summary file")
        else:
            print("\nNo conversations were successfully processed")

        # Return statistics
        return {
            'total_conversations': total_rows,
            'processed': processed_count,
            'skipped': skipped_count,
            'errors': error_count,
            'success_rate': f"{(processed_count / total_rows) * 100:.1f}%" if total_rows > 0 else "0%"
        }

    except Exception as e:
        print(f"\nError during LLM processing: {str(e)}")
        return {
            'total_conversations': 0,
            'processed': 0,
            'skipped': 0,
            'errors': 1,
            'error_message': str(e)
        }


def generate_filename(start_date: str, end_date: str, channel_id: str, file_type: str = "raw") -> str:
    """Generate filename with date and channel convention."""
    start_str = format_date_for_filename(start_date)
    end_str = format_date_for_filename(end_date)

    # Sanitize channel ID for filename
    safe_channel = re.sub(r'[^\w\-]', '_', channel_id)

    if file_type == "raw":
        return f"slack_threads_raw_{safe_channel}_{start_str}_to_{end_str}.csv"
    elif file_type == "summary":
        return f"slack_threads_summary_{safe_channel}_{start_str}_to_{end_str}.csv"
    else:
        return f"slack_threads_{file_type}_{safe_channel}_{start_str}_to_{end_str}.csv"


def log_extraction_run(log_entry: Dict[str, Any], max_log_entries: int = 1000):
    """Append a log entry to the extraction log file."""
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except:
            log_data = []
    else:
        log_data = []

    log_data.append(log_entry)

    if len(log_data) > max_log_entries:
        log_data = log_data[-max_log_entries:]
        print(f"Log file trimmed to last {max_log_entries} entries")

    with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"Log entry added to: {LOG_FILE_PATH}")


def create_log_entry(token_id: str,
                     channel_id: str,
                     start_date: str,
                     end_date: str,
                     status: str,
                     threads_count: int = 0,
                     raw_output_file: str = "",
                     summary_output_file: str = "",
                     error_message: str = "",
                     execution_time_seconds: float = 0,
                     extraction_stats: Optional[Dict] = None,
                     processing_stats: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a standardized log entry for the extraction run."""
    return {
        "run_timestamp": datetime.now().isoformat(),
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "run_time": datetime.now().strftime("%H:%M:%S"),
        "input_parameters": {
            "token_id": token_id,
            "channel_id": channel_id,
            "start_date": start_date,
            "end_date": end_date
        },
        "output": {
            "status": status,
            "threads_count": threads_count,
            "raw_output_file": raw_output_file,
            "summary_output_file": summary_output_file,
            "execution_time_seconds": round(execution_time_seconds, 2),
            "extraction_stats": extraction_stats or {},
            "processing_stats": processing_stats or {}
        },
        "error": error_message if error_message else None
    }


def get_default_date_range(days_back: int = 7) -> Tuple[str, str]:
    """Get default date range."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def run_extraction_pipeline(token: str,
                            channel_id: str,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            max_threads: Optional[int] = None,
                            skip_if_exists: bool = False,
                            process_with_llm_flag: bool = True) -> Tuple[pd.DataFrame, str, str]:
    """Run the complete Slack extraction and processing pipeline."""
    start_time = datetime.now()

    # Use default dates if not provided
    if start_date is None or end_date is None:
        start_date, end_date = get_default_date_range()

    # Generate filenames
    raw_filename = generate_filename(start_date, end_date, channel_id, file_type="raw")
    summary_filename = generate_filename(start_date, end_date, channel_id, file_type="summary")

    raw_output_path = os.path.join(BASE_OUTPUT_DIR, raw_filename)
    summary_output_path = os.path.join(BASE_OUTPUT_DIR, summary_filename)

    # Check if already exists
    if skip_if_exists and os.path.exists(raw_output_path):
        print(f"Skipping extraction: File already exists at {raw_output_path}")
        return pd.DataFrame(), raw_output_path, summary_output_path

    # Ensure output directory exists
    os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"Slack Thread Extraction & Processing Pipeline")
    print(f"{'=' * 60}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Raw output: {raw_output_path}")
    if process_with_llm_flag:
        print(f"Summary output: {summary_output_path}")

    # Initialize variables for logging
    df = pd.DataFrame()
    status = "failed"
    error_message = ""
    threads_count = 0
    extraction_stats = {}
    processing_stats = {}

    # Mask token for logging
    token_id = f"{token[:10]}...{token[-4:]}" if len(token) > 14 else "hidden"

    try:
        # Step 1: Extract threads
        print(f"\n{'=' * 40}")
        print("Step 1: Extracting Slack threads")
        print(f"{'=' * 40}")

        df, extraction_stats = extract_slack_threads(
            token=token,
            channel_id=channel_id,
            start_date=start_date,
            end_date=end_date,
            max_threads=max_threads
        )

        threads_count = len(df)

        if threads_count > 0:
            # Save raw data
            df.to_csv(raw_output_path, index=False, encoding='utf-8-sig')
            print(f"\nSuccessfully extracted {threads_count} threads")
            print(f"Saved raw data to: {raw_output_path}")

            # Step 2: Process with LLM if requested
            if process_with_llm_flag:
                print(f"\n{'=' * 40}")
                print("Step 2: Processing with LLM")
                print(f"{'=' * 40}")

                processing_stats = process_with_llm(
                    raw_file_path=raw_output_path,
                    summary_file_path=summary_output_path
                )

                if processing_stats.get('processed', 0) > 0:
                    print(f"Saved summary to: {summary_output_path}")
                    status = "success"
                else:
                    print("No conversations were processed by LLM")
                    status = "partial_success"
                    summary_output_path = ""
            else:
                status = "success"
                summary_output_path = ""
        else:
            print(f"\nNo threads found for the specified criteria")
            status = "no_data"
            raw_output_path = ""
            summary_output_path = ""

    except Exception as e:
        error_message = str(e)
        print(f"\nError during pipeline execution: {error_message}")
        print(traceback.format_exc())
        status = "failed"
        raw_output_path = ""
        summary_output_path = ""

    # Calculate execution time
    execution_time = (datetime.now() - start_time).total_seconds()

    # Create and save log entry
    log_entry = create_log_entry(
        token_id=token_id,
        channel_id=channel_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        threads_count=threads_count,
        raw_output_file=raw_output_path,
        summary_output_file=summary_output_path,
        error_message=error_message,
        execution_time_seconds=execution_time,
        extraction_stats=extraction_stats,
        processing_stats=processing_stats
    )

    log_extraction_run(log_entry)

    # Print final summary
    print(f"\n{'=' * 60}")
    print("Pipeline Summary")
    print(f"{'=' * 60}")

    if extraction_stats:
        print("\nExtraction Statistics:")
        print(f"  - Total threads: {extraction_stats['total_threads']}")
        print(f"  - Total messages: {extraction_stats['total_messages']}")
        print(f"  - Total replies: {extraction_stats['total_replies']}")
        print(f"  - Unique participants: {extraction_stats['unique_participants']}")
        print(f"  - Channel: {extraction_stats['channel_name']}")

    if processing_stats and process_with_llm_flag:
        print("\nProcessing Statistics:")
        print(f"  - Total conversations: {processing_stats.get('total_conversations', 0)}")
        print(f"  - Processed: {processing_stats.get('processed', 0)}")
        print(f"  - Skipped: {processing_stats.get('skipped', 0)}")
        print(f"  - Errors: {processing_stats.get('errors', 0)}")
        print(f"  - Success rate: {processing_stats.get('success_rate', 'N/A')}")

    print(f"\nTotal execution time: {execution_time:.2f} seconds")
    print(f"{'=' * 60}")

    return df, raw_output_path, summary_output_path


def view_extraction_history(last_n: int = 10) -> pd.DataFrame:
    """View the extraction history from the log file."""
    if not os.path.exists(LOG_FILE_PATH):
        print("No extraction history found.")
        return pd.DataFrame()

    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        if not log_data:
            print("Extraction log is empty.")
            return pd.DataFrame()

        df_log = pd.json_normalize(log_data)

        columns_to_show = [
            'run_date',
            'run_time',
            'input_parameters.channel_id',
            'input_parameters.start_date',
            'input_parameters.end_date',
            'output.status',
            'output.threads_count',
            'output.processing_stats.processed',
            'output.execution_time_seconds'
        ]

        available_columns = [col for col in columns_to_show if col in df_log.columns]
        df_log = df_log[available_columns]

        rename_dict = {
            'input_parameters.channel_id': 'channel',
            'input_parameters.start_date': 'start_date',
            'input_parameters.end_date': 'end_date',
            'output.status': 'status',
            'output.threads_count': 'threads',
            'output.processing_stats.processed': 'processed',
            'output.execution_time_seconds': 'exec_time'
        }
        df_log = df_log.rename(columns=rename_dict)

        if len(df_log) > last_n:
            print(f"Showing last {last_n} extraction runs (total: {len(df_log)})")
            df_log = df_log.tail(last_n)
        else:
            print(f"Extraction history ({len(df_log)} runs)")

        return df_log

    except Exception as e:
        print(f"Error reading log file: {e}")
        return pd.DataFrame()


def get_extraction_summary() -> Dict[str, Any]:
    """Get a summary of all extraction runs."""
    if not os.path.exists(LOG_FILE_PATH):
        return {"message": "No extraction history found"}

    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        if not log_data:
            return {"message": "Extraction log is empty"}

        total_runs = len(log_data)
        successful_runs = sum(1 for entry in log_data if entry.get('output', {}).get('status') == 'success')
        partial_success_runs = sum(
            1 for entry in log_data if entry.get('output', {}).get('status') == 'partial_success')
        failed_runs = sum(1 for entry in log_data if entry.get('output', {}).get('status') == 'failed')
        no_data_runs = sum(1 for entry in log_data if entry.get('output', {}).get('status') == 'no_data')

        total_threads = sum(entry.get('output', {}).get('threads_count', 0) for entry in log_data)
        total_processed = sum(
            entry.get('output', {}).get('processing_stats', {}).get('processed', 0)
            for entry in log_data
        )

        run_dates = [entry.get('run_date') for entry in log_data if entry.get('run_date')]
        first_run = min(run_dates) if run_dates else "N/A"
        last_run = max(run_dates) if run_dates else "N/A"

        # Get unique channels
        channels = set()
        for entry in log_data:
            channel = entry.get('input_parameters', {}).get('channel_id')
            if channel:
                channels.add(channel)

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "partial_success_runs": partial_success_runs,
            "failed_runs": failed_runs,
            "no_data_runs": no_data_runs,
            "total_threads_extracted": total_threads,
            "total_conversations_processed": total_processed,
            "unique_channels": len(channels),
            "first_run_date": first_run,
            "last_run_date": last_run,
            "success_rate": f"{((successful_runs + partial_success_runs) / total_runs) * 100:.1f}%" if total_runs > 0 else "N/A"
        }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    SLACK_TOKEN = os.getenv("SLACK_API_TOKEN", "") 
    CHANNEL_ID = "C046JUQQGUC"

    if not SLACK_TOKEN:
        print("Error: SLACK_API_TOKEN environment variable not set")
        print("Please set it using: export SLACK_API_TOKEN='your-token-here'")
        exit(1)

    print("Slack Thread Extraction & Processing Pipeline")
    print("=" * 60)
    print(f"Today's date: {datetime.now().strftime('%Y-%m-%d')}")

    # Run the complete pipeline
    df, raw_path, summary_path = run_extraction_pipeline(
        token=SLACK_TOKEN,
        channel_id=CHANNEL_ID,
        start_date="2024-11-01",  # Optional: specify start date
        end_date="2024-11-30",  # Optional: specify end date
        max_threads=None,  # Optional: limit number of threads
        skip_if_exists=False,  # Optional: skip if file exists
        process_with_llm_flag=True  # Set to False to skip LLM processing
    )

    if raw_path:
        print(f"\nRaw file: {raw_path}")
    if summary_path:
        print(f"Summary file: {summary_path}")

    print("\n" + "=" * 60)
    print("Pipeline History Summary")
    print("=" * 60)
    summary = get_extraction_summary()
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    # View recent extraction history
    print("\n" + "=" * 60)
    print("Recent Pipeline Runs")
    print("=" * 60)
    history_df = view_extraction_history(last_n=5)
    if not history_df.empty:
        print(history_df.to_string(index=False))
