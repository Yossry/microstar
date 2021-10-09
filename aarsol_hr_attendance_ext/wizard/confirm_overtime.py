from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import pdb


class OvertimeConfirm(models.TransientModel):
	_name = 'hr.overtime.confirm'
	_description = 'Overtime Confirm'

	@api.model
	def _get_overtime_ids(self):
		context = dict(self._context or {})
		active_ids = context.get('active_ids')
		overtime_ids = self.env['hr.employee.overtime'].browse(active_ids)
			
		if any(overtime.state not in ('verify') for overtime in overtime_ids):
			raise UserError("You have selected some records that are not in Verify (Cnotrol Room) State. You can select only 'Verify' records.")
		return overtime_ids and overtime_ids.ids or []
	
	overtime_ids = fields.Many2many('hr.employee.overtime','hr_overtime_confirm_rel','confirm_id','overtime_id','Overtimes',default=_get_overtime_ids)

	def view_overtimes(self):		
		return {
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'hr.employee.overtime',
			'domain': [('id', 'in', self.overtime_ids.ids),('state', 'in', ['verify']),],
			'type': 'ir.actions.act_window',
			'target': 'new',
			'nodestroy': True,
		}

	def action_confirm_overtime(self):
		overtime_ids = self.env['hr.employee.overtime'].search([('id', 'in', self.overtime_ids.ids)])
		for overtime_id in overtime_ids:
			overtime_id.action_confirm()
		return {'type': 'ir.actions.act_window_close'}