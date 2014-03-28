import datetime
import logging
from collections import defaultdict

from dateutil.parser import parse as date_parse

from .jira import Jira
from .utils import format_timedelta

log = logging.getLogger(__name__)

def accumulate_time_in_status(histories):
    """Given a dict of Jira "histories" find the ones that represent changes to
    ticket status, and accumulate the calendar time a ticket spent in a
    particular status. The time is cummulative.
    """
    accumulator = datetime.timedelta()
    starts = []
    ends = []
    for h in histories:
        for item in h['items']:
            if item['field'] == 'status':
                if item['toString'] == 'In Progress':
                    starts.append(date_parse(h['created']))
                elif item['fromString'] == 'In Progress':
                    ends.append(date_parse(h['created']))
    for start, stop in zip(starts, ends):
        accumulator += (stop - start)
    return accumulator

def main(args):
    """Main entry point of the history command. Builds jql to find closed issues
    for a given user.
    """
    log.debug("fetching history for user %s", args.username)

    j = Jira.from_config(args.cfg)
    jql = ' '.join([
        'assignee = %s AND' % args.username,
        'cf[%s] is not EMPTY AND' % j.estimate_field_id,
        'status = Closed AND',
        'resolution = Done',
        'ORDER BY updated DESC'
    ])
    issues = j.get_issue_history_by_JQL(jql)

    estimates = defaultdict(list)
    for i in issues:
        estimate = i['fields'].get("customfield_%s" % j.estimate_field_id)
        # stroll through the history
        raw_history = i.get('changelog', {}).get('histories', [])
        time_spent_in_progress = accumulate_time_in_status(raw_history)
        if estimate and time_spent_in_progress:
            estimates[estimate].append(time_spent_in_progress)

    for estimate in sorted(estimates.keys(), reverse=True):
        print "*" * 80
        print "ESTIMATE: %s" % estimate
        for t in sorted(estimates[estimate], reverse=True):
            #print t.total_seconds()
            print format_timedelta(t)

