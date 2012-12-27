from django.conf import settings
import itertools
from models import Notification, NotificationComment, user_name
from importutil import dynamic_import
from rapidsms.contrib.messaging.utils import send_message
from rapidsms.models import Connection
import logging

def get_alert_generators(type, *args, **kwargs):
    """
    Return a list of alert generators defined in the LOGISTICS_ALERT_GENERATORS
    setting.

    Return an empty list if no alert generators are defined.
    All exceptions raised while importing generators are
    allowed to propagate, to avoid masking errors.
    """
    try:
        registered_generators = getattr(settings, {
            'alert': 'LOGISTICS_ALERT_GENERATORS',
            'notif': 'LOGISTICS_NOTIF_GENERATORS',
        }[type])
    except AttributeError:
        # TODO: should this fail harder?
        registered_generators = []

    return [dynamic_import(g)(*args, **kwargs) for g in registered_generators]

def get_notifications():
    return itertools.chain(*get_alert_generators('notif'))

def trigger_notifications():
    for notif in get_notifications():
        print trigger(notif)

def trigger(notif):
    try:
        existing = Notification.objects.get(uid=notif.uid)
        #alert already generated
        #todo: add hook for amending or auto-dismissing alerts here (might not be the right place for auto-dismiss)?
        return 'alert already exists %s' % notif.uid
    except Notification.DoesNotExist:
        #new alert; save to db
        notif.initialize()
        notif.save()

        #'created' comment
        comment = NotificationComment(notification=notif, user=None, text='notification created')
        comment.save()

        def sms_send(user, content):
            try:
                conn = Connection.objects.get(contact__user=user)
            except:
                print 'user [%s] has no contact info; can\'t send sms alert' % user_name(user)
                logging.exception('error retriving contact info for user [%s]; can\'t send sms alert' % user_name(user))
                return

            send_message(conn, content)
            print 'sent sms alert to [%s]' % user_name(user)

        notif.trigger_sms(sms_send)

        return 'new alert %s' % notif

def auto_escalate():
    for notif in Notification.objects.filter(is_open=True):
        if notif.autoescalate_due():
            alert_action(notif, 'esc')
            print 'autoescalated %s' % str(notif)

def alert_action(alert, action, user=None, comment=None):
    {
        'fu': lambda a: a.followup(user),
        'esc': lambda a: a.escalate(),
        'resolve': lambda a: a.resolve(),
    }[action](alert)
    alert.save()

    if comment:
        add_user_comment(alert, user, comment)
    add_user_comment(alert, None, action_caption(action, alert, user))

def action_caption(action, alert, user):
    username = user_name(user)
    if action == 'fu':
        if alert.status == 'esc':
            return '%s claimed the escalated issue' % username
        else:
            return '%s is following up' % username
    elif action == 'esc':
        esc_class = alert.escalation_level_name(alert.escalation_level) # alert must have already been escalated
        if user is None: # auto-escalated by system
            return 'issue has been automatically escalated to %s, due to how long it has been open' % esc_class
        else:
            return '%s escalated the issue to %s' % (username, esc_class)
    elif action == 'resolve':
        return '%s resolved the issue' % username

def add_user_comment(alert, user, text):
    comment = NotificationComment(
        notification=alert,
        user=user,
        text=text
    )
    comment.save()
    return comment

def reconcile_users():
    """keep the alert userlist in sync with the underlying rules that determine
    you can see the alerts -- addresses users being added/removed from roles while
    an alert is active"""
    pass
