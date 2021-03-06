from datetime import datetime, timedelta
from os import path

import praw

import auth

__version__ = '0.1.2'

def main():
    # Init reddit
    print('Initializing reddit')
    reddit = praw.Reddit(**auth.reddit)
    subreddit = reddit.subreddit('PurplePillTest')
    pos_actions = ['approvelink', 'approvecomment']
    neg_actions = ['removelink', 'removecomment', 'spamlink', 'spamcomment']
    all_actions = pos_actions + neg_actions
    days = 30
    users = {}
    for i, log in enumerate(subreddit.mod.log(limit=None)):
        print(f'\rAnalysing logs ({i})', end='')
        # Break out of loop if log entries are too old
        dt = datetime.fromtimestamp(log.created_utc)
        delta = datetime.utcnow() - dt
        if delta > timedelta(days=days):
            break
        # Filter actions
        if log.action not in all_actions:
            continue
        # Action counter
        users.setdefault(log.target_author, {})
        user = users[log.target_author]
        for action in all_actions:
            user.setdefault(action, 0)
        user[log.action] += 1
        # Positive/neagtive and total action counter
        user.setdefault('pos', 0)
        user.setdefault('neg', 0)
        user.setdefault('total', 0)
        if log.action in pos_actions:
            user['pos'] += 1
        elif log.action in neg_actions:
            user['neg'] += 1
        user['total'] += 1
    # Sort by total action count
    print('\nSorting data')
    users = dict(sorted(users.items(), key=lambda u: u[1]['neg'], reverse=True))
    # Build message
    print('Building mod mail message')
    message = f'#### Mod log summary for the last {days} days\n\n'
    message += 'Rank | Username | remove/spam | approve\n'
    message += '-: | - | -: | -:\n'
    for i, (user, counter) in enumerate(users.items()):
        message += '{rank} | [{user}](https://reddit.com/u/{user}) | {neg} | {pos}\n'.format(
            rank=i+1, user=user, neg=counter['neg'], pos=counter['pos'])
    # Send modmail
    print('Sending message (clipped to max. 9,000 characters)')
    # Limit modmail to 9k characters, the actual upper limit should be 10k but better be safe
    subreddit.message('Mod log summary', message[:9000])
    # Write the whole message to file
    filepath = path.join(path.dirname(__file__), 'modlogs.md')
    print(f'Writing the whole message to {filepath}')
    with open(filepath, 'w') as f:
        f.write(message)

if __name__ == "__main__":
    main()
