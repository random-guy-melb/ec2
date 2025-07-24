from __future__ import annotations
from typing import List, Dict, Tuple, Any, Optional
from dateutil.parser import parse
from jira import JIRA
from tqdm import tqdm
from datetime import datetime, timedelta
import traceback

import pandas as pd
import json
import re
import os

# from projects.jira.configs import configuration

MAX_EVENTS = 400  # keep at most N history items per bug
CTRL_REGEX = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]')
TEAM_FIELD_ID = "customfield_11731"


# IMPORTANT: For production use, store API_TOKEN as an environment variable:
# API_TOKEN = os.environ.get('JIRA_API_TOKEN')

# Base directory for saving data
BASE_OUTPUT_DIR = "./csv_data"
# Log file path
LOG_FILE_PATH = "./csv_data/extraction_log.json"


def clean_text(t: str | None) -> str:
    """Strip ASCII control chars except tab / newline."""
    if not t:
        return ""
    return CTRL_REGEX.sub("", t)


def calc_days(start, end) -> int | None:
    if not (start and end):
        return None
    try:
        return (parse(end) - parse(start)).days
    except Exception:
        return None


def safe(obj, *attrs, default=""):
    for a in attrs:
        if hasattr(obj, a):
            v = getattr(obj, a)
            if v:
                return v
        if isinstance(obj, dict):
            for a in attrs:
                if obj.get(a):
                    return obj[a]
    return default


def get_versions(issue, field_key="versions") -> str:
    vers = issue.raw["fields"].get(field_key, [])
    return ", ".join([safe(v, "name") for v in vers]) if vers else ""


def get_linked_issues(issue, field_key="issuelinks") -> str:
    linkedissue = issue.raw["fields"].get(field_key, [])
    if isinstance(linkedissue, list):
        linkedissue = " ".join(linkedissue)
    return linkedissue


def get_sprint(issue, field_key="customfield_10004") -> str:
    sprint = issue.raw["fields"].get(field_key, [])
    if isinstance(sprint, list) and sprint:
        print(sprint)
        try:
            sprint = " ".join(sprint)
        except:
            sprint = " ".join(sprint[0].get("name", "Not Found"))
    return sprint


def get_epicandtheme(issue, field_key="customfield_10113") -> str:
    epic_theme = issue.raw.get("customfield_10113", {}).get(field_key, [])
    if isinstance(epic_theme, list):
        epic_theme = " ".join(epic_theme)
    return epic_theme


def get_epic(issue, field_key="customfield_10000") -> str:
    epic_name = issue.raw.get("customfield_10000", {}).get(field_key, [])
    if isinstance(epic_name, list):
        epic_name = " ".join(epic_name)
    return epic_name


def get_repo(issue) -> str:
    patt = r'https?://(?:www\.)?(?:github|bitbucket|gitlab)\.com/[\w\-\.]+/[\w\-\.]+'
    for source in [issue.fields.description] + [
        getattr(c, "body", "") for c in getattr(issue.fields.comment, "comments", [])
    ]:
        if not source:
            continue
        m = re.search(patt, source)
        if m:
            return m.group(0)
    return ""


def build_timeline(issue) -> Tuple[List[Dict[str, Any]], List[Dict]]:
    timeline, status_hist = [], []
    timeline.append(dict(
        date=issue.fields.created,
        author=safe(issue.fields.reporter, "displayName", "name"),
        type="creation",
        event="Created"
    ))

    if hasattr(issue, "changelog"):
        for h in issue.changelog.histories:
            when = h.created
            who = safe(h.author, "displayName", "name")
            for i in h.items:
                entry = dict(
                    date=when,
                    author=who,
                    type="change",
                    field=i.field,
                    frm=clean_text(i.fromString),
                    to=clean_text(i.toString)
                )
                timeline.append(entry)
                if i.field.lower() == "status":
                    status_hist.append(entry)

    # comments (optional, can comment this block out if noise)
    for c in getattr(issue.fields.comment, "comments", []):
        try:
            comment = clean_text(c.body)[:500]  # cap long comments
        except:
            print("Skipped comment.")
            continue
        timeline.append(dict(
            date=c.created,
            author=safe(c.author, "displayName", "name"),
            type="comment",
            event=comment
        ))

    # chronological order
    timeline.sort(key=lambda x: parse(x["date"]))

    # enforce MAX_EVENTS (keeps first & last)
    if len(timeline) > MAX_EVENTS:
        timeline = timeline[:MAX_EVENTS // 2] + timeline[-MAX_EVENTS // 2:]

    return timeline, status_hist


def to_json_safe(obj) -> str:
    """
    Serialise to JSON **and** guarantee it parses back.
    If it fails (shouldn't), returns empty string.
    """
    try:
        txt = json.dumps(obj, ensure_ascii=False, default=str)
        json.loads(txt)
        return txt
    except Exception as e:
        print("⚠️ bad JSON, skipping timeline:", e)
        return ""


def format_date_for_jql(date_input: str | datetime) -> str:
    """
    Format a date for JQL queries.
    Accepts string or datetime object and returns formatted string.
    """
    if isinstance(date_input, str):
        # Parse the string to datetime
        dt = datetime.strptime(date_input, "%Y-%m-%d") if "-" in date_input else datetime.strptime(date_input,
                                                                                                   "%Y/%m/%d")
    else:
        dt = date_input

    # Format as required by JQL (yyyy-MM-dd HH:mm)
    return dt.strftime("%Y-%m-%d %H:%M")


def extract_bugs(jira: JIRA,
                 projects: List[str] | None = None,
                 max_results: int = 1000,
                 max_char_len: int = 28000,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 date_field: str = "created") -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Extract bugs from Jira with optional date filtering.

    Parameters:
    -----------
    jira : JIRA
        JIRA connection object
    projects : List[str] | None
        List of project keys to filter by
    max_results : int
        Maximum number of results to return
    max_char_len : int
        Maximum character length for text fields
    start_date : Optional[str]
        Start date in format "YYYY-MM-DD" (inclusive)
    end_date : Optional[str]
        End date in format "YYYY-MM-DD" (inclusive)
    date_field : str
        The date field to filter by: "created", "updated", or "resolved"
        Default is "created"

    Returns:
    --------
    Tuple[pd.DataFrame, Dict[str, str]]
        DataFrame of bugs and dictionary of timelines
    """

    # Build base JQL query
    jql_parts = ["issuetype = Bug"]

    # Add project filter if specified
    if projects:
        jql_parts.append(f"project in ({', '.join(projects)})")

    # Add date filters if specified
    if start_date:
        # Format the start date for JQL (beginning of day)
        start_formatted = f"{start_date} 00:00"
        jql_parts.append(f'{date_field} >= "{start_formatted}"')

    if end_date:
        # Format the end date for JQL (end of day)
        end_formatted = f"{end_date} 23:59"
        jql_parts.append(f'{date_field} <= "{end_formatted}"')

    # Combine all JQL parts
    jql = " AND ".join(jql_parts)

    # Add ordering by the date field
    jql += f" ORDER BY {date_field} ASC"

    bugs, timelines = [], {}
    start, total = 0, None
    print("🔍", jql)

    # Print date range info if provided
    if start_date or end_date:
        date_info = f"📅 Filtering by {date_field} date: "
        if start_date and end_date:
            date_info += f"from {start_date} to {end_date}"
        elif start_date:
            date_info += f"from {start_date} onwards"
        else:
            date_info += f"up to {end_date}"
        print(date_info)

    while True:
        issues = jira.search_issues(
            jql, startAt=start, maxResults=100,
            fields=f"summary,status,created,updated,resolutiondate,priority,project,issuetype,linkedissue,"
                   f"customfield_10113,customfield_10000,customfield_10001,customfield_10002,customfield_10004,"
                   f"Sprint,"
                   f"versions,fixVersions,description,comment,assignee,reporter,{TEAM_FIELD_ID}",
            expand="changelog"
        )

        if total is None:
            total = issues.total or 0
        if not issues:
            break

        for iss in tqdm(issues, desc=f"{start + len(issues)}/{total}"):
            tl, status_hist = build_timeline(iss)
            tl_json = to_json_safe(tl)
            if len(str(tl_json)) > max_char_len:
                continue

            bugs.append(dict(
                BugID=iss.key,
                Summary=iss.fields.summary,
                Status=iss.fields.status.name,
                Project=iss.fields.project.name,
                ProjectCode=iss.fields.project.key,
                ProjectID=iss.fields.project.id,
                Created=iss.fields.created,
                Updated=iss.fields.updated,
                Closed=iss.fields.resolutiondate or "",
                Priority=safe(iss.fields.priority, "name"),
                Reporter=safe(iss.fields.reporter, "displayName", "name"),
                Assignee=safe(iss.fields.assignee, "displayName", "name", default="Unassigned"),
                Description=clean_text(iss.fields.description or "")[:max_char_len],
                IntroducedVersion=get_versions(iss, "versions"),
                FixVersion=get_versions(iss, "fixVersions"),
                LinkedIssue=get_linked_issues(iss, "linkedissue"),
                Sprint=get_sprint(iss, "customfield_10004"),
                EpicAndTheme=get_epicandtheme(iss, "customfield_10113"),
                Epic=get_epic(iss, "customfield_10000"),
                Team=safe(getattr(iss.fields, TEAM_FIELD_ID, ""), "value", "name"),
                Repository=get_repo(iss),
                StatusFlow=" -> ".join([e["to"] for e in status_hist]),
                TimelineJSON=tl_json,
                DefectAging=calc_days(iss.fields.created, iss.fields.resolutiondate),
                DaysToLastUpdate=calc_days(iss.fields.created, iss.fields.updated),
                TotalStatusChanges=len(status_hist),
                CommentCount=len(getattr(iss.fields.comment, "comments", [])),
            ))

            timelines[iss.key] = tl_json
            if len(bugs) >= max_results:
                break

        if len(bugs) >= max_results or start + len(issues) >= total:
            break
        start += len(issues)

    return pd.DataFrame(bugs), timelines


def save_df(df: pd.DataFrame, path="jira_bugs.csv"):
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print("💾 CSV:", path)


def save_timelines(tl: Dict[str, str], path="bug_timelines.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for bug, js in tl.items():
            f.write(json.dumps({"bug": bug, "timeline": js}, ensure_ascii=False) + "\n")
    print("💾 timelines:", path)


def get_default_date_range() -> Tuple[str, str]:
    """
    Get default date range:
    - End date: 3 days before today
    - Start date: 1 day before end date

    Example: If today is 2025-07-24
    - End date will be 2025-07-21
    - Start date will be 2025-07-20

    Returns:
    --------
    Tuple[str, str]: (start_date, end_date) in "YYYY-MM-DD" format
    """
    today = datetime.now()
    end_date = today - timedelta(days=3)
    start_date = end_date - timedelta(days=1)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def generate_filename(start_date: str, end_date: str, prefix: str = "jira_bugs", extension: str = "csv") -> str:
    """
    Generate filename with date convention for cloud storage.

    Parameters:
    -----------
    start_date : str
        Start date in "YYYY-MM-DD" format
    end_date : str
        End date in "YYYY-MM-DD" format
    prefix : str
        File prefix (default: "jira_bugs")
    extension : str
        File extension (default: "csv")

    Returns:
    --------
    str: Filename in format "{prefix}_YYYYMMDD_to_YYYYMMDD.{extension}"
    """
    # Convert dates to filename format
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    return f"{prefix}_{start_str}_to_{end_str}.{extension}"


def log_extraction_run(log_entry: Dict[str, Any], max_log_entries: int = 1000):
    """
    Append a log entry to the extraction log file.

    Parameters:
    -----------
    log_entry : Dict[str, Any]
        Dictionary containing log information
    max_log_entries : int
        Maximum number of log entries to keep (default: 1000)
        Older entries are removed when limit is exceeded
    """
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    # Read existing log if it exists
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except:
            log_data = []
    else:
        log_data = []

    # Append new entry
    log_data.append(log_entry)

    # Keep only the most recent entries if exceeding max
    if len(log_data) > max_log_entries:
        log_data = log_data[-max_log_entries:]
        print(f"📝 Log file trimmed to last {max_log_entries} entries")

    # Write updated log
    with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"📝 Log entry added to: {LOG_FILE_PATH}")


def create_log_entry(start_date: str,
                     end_date: str,
                     date_field: str,
                     projects: Optional[List[str]],
                     status: str,
                     bugs_count: int = 0,
                     output_file: str = "",
                     error_message: str = "",
                     execution_time_seconds: float = 0) -> Dict[str, Any]:
    """
    Create a standardized log entry for the extraction run.

    Parameters:
    -----------
    start_date : str
        Start date of extraction
    end_date : str
        End date of extraction
    date_field : str
        Date field used for filtering
    projects : Optional[List[str]]
        List of projects filtered (if any)
    status : str
        "success", "failed", or "no_data"
    bugs_count : int
        Number of bugs extracted
    output_file : str
        Path to output file (if created)
    error_message : str
        Error message if failed
    execution_time_seconds : float
        Time taken to execute

    Returns:
    --------
    Dict[str, Any]: Log entry dictionary
    """
    return {
        "run_timestamp": datetime.now().isoformat(),
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "run_time": datetime.now().strftime("%H:%M:%S"),
        "input_parameters": {
            "start_date": start_date,
            "end_date": end_date,
            "date_field": date_field,
            "projects": projects or []
        },
        "output": {
            "status": status,
            "bugs_count": bugs_count,
            "output_file": output_file,
            "execution_time_seconds": round(execution_time_seconds, 2)
        },
        "error": error_message if error_message else None
    }


def run_extraction(start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   date_field: str = "resolutiondate",
                   max_results: int = 1000,
                   projects: Optional[List[str]] = None,
                   skip_if_exists: bool = False) -> Tuple[pd.DataFrame, str]:
    """
    Run the Jira bug extraction with specified or default parameters.

    Parameters:
    -----------
    start_date : Optional[str]
        Start date in "YYYY-MM-DD" format. If None, uses default calculation.
    end_date : Optional[str]
        End date in "YYYY-MM-DD" format. If None, uses default calculation.
    date_field : str
        The date field to filter by: "created", "updated", or "resolved"
    max_results : int
        Maximum number of results to return
    projects : Optional[List[str]]
        List of project keys to filter by
    skip_if_exists : bool
        If True, skip extraction if date range was already successfully extracted

    Returns:
    --------
    Tuple[pd.DataFrame, str]: (DataFrame of bugs, output file path)
    """
    # Track execution time
    start_time = datetime.now()

    # Use default dates if not provided
    if start_date is None or end_date is None:
        start_date, end_date = get_default_date_range()

    # Check if already extracted (if requested)
    if skip_if_exists and check_date_range_extracted(start_date, end_date, date_field):
        print(f"⏭️  Skipping extraction: Date range {start_date} to {end_date} already extracted successfully")
        filename = generate_filename(start_date, end_date, prefix="jira_bugs")
        output_path = os.path.join(BASE_OUTPUT_DIR, filename)
        print(f"📁 Existing file: {output_path}")
        return pd.DataFrame(), output_path

    # Generate filename
    filename = generate_filename(start_date, end_date, prefix="jira_bugs")
    output_path = os.path.join(BASE_OUTPUT_DIR, filename)

    # Ensure output directory exists
    os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

    print(f"📅 Extracting bugs from {start_date} to {end_date}")
    print(f"📁 Output file: {output_path}")

    # Initialize variables for logging
    df = pd.DataFrame()
    status = "failed"
    error_message = ""
    bugs_count = 0

    try:
        # Initialize JIRA connection
        jira = JIRA(server=JIRA_URL, basic_auth=(ADMIN_EMAIL, API_TOKEN))

        # Extract bugs
        df, tl = extract_bugs(
            jira,
            projects=projects,
            max_results=max_results,
            start_date=start_date,
            end_date=end_date,
            date_field=date_field
        )

        bugs_count = len(df)

        # Save if data found
        if bugs_count > 0:
            save_df(df, output_path)
            print(f"\n✅ Successfully extracted {bugs_count} bugs")
            status = "success"
        else:
            print(f"\n⚠️  No bugs found for the specified criteria")
            status = "no_data"
            output_path = ""  # No file created

    except Exception as e:
        error_message = str(e)
        print(f"\n❌ Error during extraction: {error_message}")
        print(traceback.format_exc())
        status = "failed"
        output_path = ""  # No file created

    # Calculate execution time
    execution_time = (datetime.now() - start_time).total_seconds()

    # Create and save log entry
    log_entry = create_log_entry(
        start_date=start_date,
        end_date=end_date,
        date_field=date_field,
        projects=projects,
        status=status,
        bugs_count=bugs_count,
        output_file=output_path,
        error_message=error_message,
        execution_time_seconds=execution_time
    )

    log_extraction_run(log_entry)

    return df, output_path


def view_extraction_history(last_n: int = 10) -> pd.DataFrame:
    """
    View the extraction history from the log file.

    Parameters:
    -----------
    last_n : int
        Number of recent entries to display (default: 10)

    Returns:
    --------
    pd.DataFrame: DataFrame with extraction history
    """
    if not os.path.exists(LOG_FILE_PATH):
        print("📝 No extraction history found.")
        return pd.DataFrame()

    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        if not log_data:
            print("📝 Extraction log is empty.")
            return pd.DataFrame()

        # Convert to DataFrame for easy viewing
        df_log = pd.json_normalize(log_data)

        # Select and rename columns for clarity
        columns_to_show = [
            'run_date',
            'run_time',
            'input_parameters.start_date',
            'input_parameters.end_date',
            'input_parameters.date_field',
            'output.status',
            'output.bugs_count',
            'output.execution_time_seconds'
        ]

        # Check which columns exist
        available_columns = [col for col in columns_to_show if col in df_log.columns]
        df_log = df_log[available_columns]

        # Rename columns for better readability
        rename_dict = {
            'input_parameters.start_date': 'start_date',
            'input_parameters.end_date': 'end_date',
            'input_parameters.date_field': 'date_field',
            'output.status': 'status',
            'output.bugs_count': 'bugs_count',
            'output.execution_time_seconds': 'exec_time_sec'
        }
        df_log = df_log.rename(columns=rename_dict)

        # Show last N entries
        if len(df_log) > last_n:
            print(f"📊 Showing last {last_n} extraction runs (total: {len(df_log)})")
            df_log = df_log.tail(last_n)
        else:
            print(f"📊 Extraction history ({len(df_log)} runs)")

        return df_log

    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        return pd.DataFrame()


def get_extraction_summary() -> Dict[str, Any]:
    """
    Get a summary of all extraction runs.

    Returns:
    --------
    Dict[str, Any]: Summary statistics
    """
    if not os.path.exists(LOG_FILE_PATH):
        return {"message": "No extraction history found"}

    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        if not log_data:
            return {"message": "Extraction log is empty"}

        # Calculate summary statistics
        total_runs = len(log_data)
        successful_runs = sum(1 for entry in log_data if entry.get('output', {}).get('status') == 'success')
        failed_runs = sum(1 for entry in log_data if entry.get('output', {}).get('status') == 'failed')
        no_data_runs = sum(1 for entry in log_data if entry.get('output', {}).get('status') == 'no_data')
        total_bugs = sum(entry.get('output', {}).get('bugs_count', 0) for entry in log_data)

        # Get date range of extractions
        run_dates = [entry.get('run_date') for entry in log_data if entry.get('run_date')]
        first_run = min(run_dates) if run_dates else "N/A"
        last_run = max(run_dates) if run_dates else "N/A"

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "no_data_runs": no_data_runs,
            "total_bugs_extracted": total_bugs,
            "first_run_date": first_run,
            "last_run_date": last_run,
            "success_rate": f"{(successful_runs / total_runs) * 100:.1f}%" if total_runs > 0 else "N/A"
        }

    except Exception as e:
        return {"error": str(e)}


def check_date_range_extracted(start_date: str, end_date: str, date_field: str = "created") -> bool:
    """
    Check if a specific date range has already been successfully extracted.

    Parameters:
    -----------
    start_date : str
        Start date in "YYYY-MM-DD" format
    end_date : str
        End date in "YYYY-MM-DD" format
    date_field : str
        The date field to check (default: "created")

    Returns:
    --------
    bool: True if date range was already successfully extracted
    """
    if not os.path.exists(LOG_FILE_PATH):
        return False

    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        for entry in log_data:
            params = entry.get('input_parameters', {})
            output = entry.get('output', {})

            if (params.get('start_date') == start_date and
                    params.get('end_date') == end_date and
                    params.get('date_field') == date_field and
                    output.get('status') == 'success'):
                return True

        return False

    except Exception:
        return False


if __name__ == "__main__":
    # Default execution: Automatic date calculation
    # End date: 3 days before today
    # Start date: 1 day before end date

    print("Jira Bug Extractor - Automatic Date Range")
    print("=" * 60)
    print(f"Today's date: {datetime.now().strftime('%Y-%m-%d')}")

    # Run extraction with default dates
    df, output_path = run_extraction()

    if output_path:
        print(f"\n File ready for download: {output_path}")

    # Display extraction history summary
    print("\n" + "=" * 60)
    print("Extraction History Summary")
    print("=" * 60)
    summary = get_extraction_summary()
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
