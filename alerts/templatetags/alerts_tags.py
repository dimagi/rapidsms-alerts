from django import template
from alerts.utils import get_alert_generators
from django.template import RequestContext
import itertools
from django.template.loader import render_to_string
from alerts.models import Notification
register = template.Library()
import json

@register.inclusion_tag("alerts/partials/alerts.html", takes_context=True)
def alerts(context, request):
    alerts = itertools.chain(*(g for g in get_alert_generators('alert', request=request, context=context) if g is not None))
    return {"alerts": alerts}

@register.simple_tag(takes_context=True)
def notifications(context, request):
    notifs = Notification.objects.filter(is_open=True, visible_to__user=request.user)
    data = json.dumps([notif.json(request.user) for notif in notifs])

    return render_to_string("alerts/partials/notifications.html",
                            {"notifs": notifs,
                             "notif_data": data}, context_instance=RequestContext(request))

