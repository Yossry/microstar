from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import pdb


class OvertimeApprov(models.TransientModel):
	_name = 'hr.overtime.approve'
	_description = 'Overtime Approval'

	@api.model
	def _get_overtime_ids(self):
		context = dict(self._context or {})
		active_ids = context.get('active_ids')
		overtime_ids = self.env['hr.employee.overtime'].browse(active_ids)
			
		if any(overtime.state not in ('confirm') for overtime in overtime_ids):
			raise UserError("You have selected some records that are not in Confirm state. You can select only 'Confirm' records.")
		return overtime_ids and overtime_ids.ids or []
	
	overtime_ids = fields.Many2many('hr.employee.overtime','hr_overtime_approve_rel','approve_id','overtime_id','Overtimes',default=_get_overtime_ids)

	def view_overtimes(self):		
		return {
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'hr.employee.overtime',
			'domain': [('id', 'in', self.overtime_ids.ids),('state', 'in', ['confirm']),],
			'type': 'ir.actions.act_window',
			'target': 'new',
			'nodestroy': True,
		}

	def action_approve_overtime(self):
		overtime_ids = self.env['hr.employee.overtime'].search([('id', 'in', self.overtime_ids.ids)])
		for overtime_id in overtime_ids:
			overtime_id.action_approve()
		return {'type': 'ir.actions.act_window_close'}