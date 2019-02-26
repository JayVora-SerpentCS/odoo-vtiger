import json
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT
from datetime import datetime
from datetime import timedelta
from urllib.request import urlopen
from urllib.request import Request
from urllib.parse import urlencode


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_calendar_event()

    @api.multi
    def sync_vtiger_calendar_event(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = ("""SELECT * FROM Events WHERE modifiedtime >= '%s';"""
                   % (company.last_sync_date))
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request('%s?%s' % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            if result.get('success'):
                calendar_obj = self.env['calendar.event']
                for res in result.get('result', []):
                    calendar_vals = {
                        'name': res.get('subject'),
                        'state': 'draft',
                    }
                    if res.get('recurringtype') != '--None--':
                        calendar_vals.update(
                            {'recurrency': bool(res.get('recurringtype', '')),
                             'rrule_type': res.get('recurringtype', '').lower(),})
##                    setting the time duration
                    get_start_time = res.get('time_start')
                    get_start_date = res.get('date_start')
                    get_date = str(get_start_date)
                    if get_start_date:
                        start_date = datetime.strptime(get_date, DT)
                    get_end_date = res.get('due_date')
                    if get_end_date:
                        get_en_date = str(get_end_date)
                        end_date = datetime.strptime(get_en_date, DT)
                    if get_start_date and get_end_date and \
                       get_start_date > get_end_date:
                        calendar_vals.update({
                             'start': str(start_date),
#                             'stop': start_date,
                        })
                    if get_start_date and get_end_date and \
                       get_start_date < get_end_date:

                        calendar_vals.update({
                             'start': str(start_date),
                             'stop': str(end_date),
                             'allday': True,
                        })
#                    temp_calendar_vals1.update({
#                         'start': end_date,
#                         'stop': start_date,
#                         'name': 'dfdfdfd',
#                         'duration':0.0,
#                    })
#                    if get_start_date and get_end_date and\
#                       get_start_date > get_end_date:
#                        calendar_vals.update({
#                             'start': start_date,
#                             'stop': start_date,
#                        })
                    else:
                        duration_hours = int(res.get('duration_hours'))
                        duration_minutes = int(res.get('duration_minutes'))
                        hr = abs(duration_hours)
                        min = abs(duration_minutes)
                        total_duration  = float(str ( str(hr)+ '.'+ str(min)))
                        split_time = str(get_start_time).split(':')
                        hour = int(split_time[0])
                        minute = int(split_time[1])
                        second = int(split_time[2])
                        date_s = datetime.strptime(get_date, DT) + \
                            timedelta(hours=hour,minutes=minute,seconds=second)
                        date_stp = date_s + timedelta(days=1)
                        duration = calendar_obj._get_duration(str(date_s), 
                                                              str(date_stp))
                        calendar_vals.update({
                            'start': str(date_s),
                            'start_datetime':str(date_s),
#                            'stop': end_date,
#                            'duration': duration,
                            'allday': False,
                        })
                        if not calendar_vals.get('stop'):
                            calendar_vals.update({
                            'stop': str(date_stp),
                            'stop_datetime': str(date_stp)
                        })
#                        temp_calendar_vals.update({
#                            'start_datetime': date_s,
#                            'duration': total_duration,
#                            'start': start_date,
#                            'stop': start_date,
#                            'allday': False,
#                        })
#                    user_id = res.get('assigned_user_id')
#                    if user_id:
#                        user = user_obj.search(
#                            [('vtiger_id', '=', user_id)], limit=1
#                        )
#                        if user:
#                            calendar_vals.update({'partner_id': partner.id})
                    # Search for existing sale order
                    calendar_event = calendar_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1
                    )
                    if calendar_event:
                        calendar_event.write(calendar_vals)
                    else:
                        calendar_vals.update({
                            'vtiger_id': res.get('id'),
                        })
                        dd = calendar_vals.get('stop')
                        uid = self._context.get('uid')
                        user_rec = self.env['res.users'].browse(uid)
#                        kll = self._context.get('tz') 
#                        tz = pytz.timezone(user_rec.partner_id.tz) or pytz.utc
#                        date_stop = pytz.utc.localize(dd).astimezone(tz)
#                        calendar_vals.update({
#                            'start_datetime': calendar_vals.get('start'),
#                            'start_datetime': calendar_vals.get('start'),
#                        })
                        calendar_obj.create(calendar_vals)
        return True