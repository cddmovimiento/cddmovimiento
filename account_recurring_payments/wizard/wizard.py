# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mashood K.U (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class RecurringPaymentsWizard(models.TransientModel):
    _name = 'recurring.payments.wizard'

    recurring_lines = fields.Many2many('account.recurring.entries.line')
    date_from = fields.Date('Starting Date', default=date.today())
    date_to = fields.Date('Ending Date', default=date.today())

    @api.onchange('date_from', 'date_to')
    def get_remaining_entries(self):
        self.recurring_lines = None
        data = self.env['account.recurring.payments'].search(
            [('state', '=', 'running')])
        entries = self.env['account.move'].search([('is_active', '=', True)])
        journal_dates = []
        journal_codes = []
        remaining_dates = []
        for entry in entries:
            journal_dates.append(str(entry.date))
            if entry.recurring_internal_ref:
                journal_codes.append(str(entry.recurring_internal_ref))
        today = datetime.today()
        converted_date_from = datetime.strptime(str(self.date_from),
                                                '%Y-%m-%d')
        ending_date = datetime.strptime(str(self.date_to), '%Y-%m-%d')
        for line in data:
            if line.date:
                recurr_dates = []
                start_date = datetime.strptime(str(line.date), '%Y-%m-%d')
                ending_dates = datetime.strptime(str(line.end_date),
                                                 '%Y-%m-%d')
                while start_date <= ending_dates:
                    recurr_dates.append(str(start_date.date()))
                    if line.recurring_period == 'days':
                        start_date += relativedelta(
                            days=int(line.recurring_interval))
                    elif line.recurring_period == 'weeks':
                        start_date += relativedelta(
                            weeks=int(line.recurring_interval))
                    elif line.recurring_period == 'months':
                        start_date += relativedelta(
                            months=int(line.recurring_interval))
                    else:
                        start_date += relativedelta(
                            years=int(line.recurring_interval))
                for rec in recurr_dates:
                    recurr_code = str(line.id) + '/' + str(rec)
                    converted_rec = datetime.strptime(str(rec), '%Y-%m-%d')
                    if recurr_code not in journal_codes:
                        date_time_obj = datetime.strptime(rec,
                                                          '%Y-%m-%d')
                        if date_time_obj <= ending_date:
                            remaining_dates.append((0, 0, {
                                'date': rec,
                                'template_name': line.name,
                                'amount': line.amount,
                                'tmpl_id': line.id,
                            }))
        self.recurring_lines = remaining_dates

    def generate_payment(self):
        data = self.recurring_lines
        if not data:
            raise UserError(_("There is no remaining payments"))
        for line in data:
            this = line.tmpl_id
            recurr_code = str(this.id) + '/' + str(line.date)
            rec = str(this.journal_id.name) + ' / ' + str(line.id)
            line_ids = [(0, 0, {
                'account_id': this.credit_account.id,
                'partner_id': this.partner_id.id,
                'credit': line.amount,
                'name': 'Recurring Entry'
            }), (0, 0, {
                'account_id': this.debit_account.id,
                'partner_id': this.partner_id.id,
                'debit': line.amount,
                'name': 'Recurring Entry'
            })]

            vals = ({
                'date': line.date,
                'recurring_internal_ref': recurr_code,
                'company_id': self.env.user.company_id.id,
                'journal_id': this.journal_id.id,
                'is_active': True,
                'state': 'draft',
                'ref': line.template_name,
                'line_ids': line_ids
            })
            mv = self.env['account.move'].create(vals)
            if this.journal_state == 'posted':
                mv.action_post()
                line.tmpl_id.final_posted_date = line.date
            else:
                line.tmpl_id.final_posted_date = line.date


class GetAllRecurringEntries(models.TransientModel):
    _name = 'account.recurring.entries.line'

    date = fields.Date('Date')
    template_name = fields.Char('Name')
    amount = fields.Float('Amount')
    tmpl_id = fields.Many2one('account.recurring.payments', string='id')
    p_id = fields.Many2one('recurring.payments.wizard')
