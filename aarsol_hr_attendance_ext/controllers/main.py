# -*- coding: utf-8 -*-

import time
from odoo.addons.mail.controllers.main import MailController
from datetime import date , datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT
from pytz import timezone, utc
from dateutil.relativedelta import relativedelta
from odoo import fields, http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo import release

# http://pythonhosted.org/ranking/      easy_install ranking
#import ranking 
import pdb

def strToDatetime(strdatetime):
	return datetime.strptime(strdatetime, '%Y-%m-%d %H:%M:%S')

def utcDate(self, ddate):
	user = self.env.user
	local_tz = timezone(user.tz)
	local_date = local_tz.localize(ddate, is_dst=False)
	utc_date = local_date.astimezone(utc)
	return utc_date			

def localDate(self, utc_dt):
	user = self.env.user
	local_tz = timezone(user.tz)
	local_dt = utc_dt.replace(tzinfo=utc).astimezone(local_tz)
	return local_dt			

def parse_date(td):
	resYear = float(td.days)/365.0                  
	resMonth = (resYear - int(resYear))*365.0/30.0 
	resDays = int((resMonth - int(resMonth))*30)
	resYear = int(resYear)
	resMonth = int(resMonth)
	return (resYear and (str(resYear) + "Y ") or "") + (resMonth and (str(resMonth) + "M ") or "") + (resMonth and (str(resDays) + "D") or "")

def compute_duration(ddate):
	start = datetime.strptime(ddate,OE_DFORMAT)
	end = datetime.strptime(time.strftime(OE_DFORMAT),OE_DFORMAT)	
	delta = end - start
	return parse_date(delta)

class HrEmployeeOvertimeController(http.Controller):

	@http.route('/hr_attendance_ext/validate2', type='http', auth='public', methods=['GET'])
	def hr_employee_overtime_validate(self, res_id, token):
		comparison, record, redirect = MailController._check_token_and_record_or_redirect('hr.employee.overtime', int(res_id), token)
		if comparison and record:
			try:
				record.action_approve()
			except Exception:
				return MailController._redirect_to_messaging()
		return redirect

class OverTimeDashboard(http.Controller):

	@http.route('/overtime_dashboard/data', type='json', auth='user')
	def overtime_dashboard_data(self, userid=0):
		
		#if not request.env.user.has_group('base.group_erp_manager'):
		#	raise AccessError("Access Denied")

		cr = request.cr
		
		if userid == 0:
			userinfo = request.env['hr.employee'].search([('user_id','=',request.env.user.id)])
		else:	
			userinfo = request.env['hr.employee'].search([('code','=',str(userid).zfill(4))])
		
		if not userinfo:
			userinfo = request.env['hr.employee'].search([('user_id','=',request.env.user.id)])
			
		if not userinfo:	
			userinfo = request.env['hr.employee'].search([('code','=','0003')])
	
		sql = """select * from hr_overtime_report_employee_duration where employee = %s """ % (userinfo.id,)
		cr.execute(sql)
		if cr.rowcount > 0:
			emp_hours = cr.fetchall()[0]
			emp_hours = [0 if v is None else float("{0:.0f}".format(v)) for v in emp_hours]
			emp_hours.pop(0)
		else:
			emp_hours = [0 for i in range(12)]			
		emp_hours_total = sum(emp_hours)
		
		sql = """select * from hr_overtime_report_employee_amount where employee = %s """ % (userinfo.id,)			
		cr.execute(sql)
		if cr.rowcount > 0:
			emp_cost = cr.fetchall()[0]
		else:
			emp_cost = [0 for i in range(13)]			
		
		rank_cost = [0 if v is None else int(v) for v in emp_cost] 
		rank_cost_total = [0 if v is None else v for v in emp_cost] 
		emp_cost = [0 if v is None else float("{0:.0f}".format(v)) for v in emp_cost]
		emp_cost.pop(0)
		rank_cost.pop(0)
		rank_cost_total.pop(0)
		
		emp_cost_total = sum(emp_cost)
		emp_rank_cost_total = sum(rank_cost_total)
		
		sql = """select * from hr_overtime_report_employee_cnt where employee = %s """ % (userinfo.id,)					
		cr.execute(sql)
		if cr.rowcount > 0:		
			emp_cnt = cr.fetchall()[0]
			emp_cnt = [0 if v is None else v for v in emp_cnt]
			emp_cnt.pop(0)
		else:
			emp_cnt = [0 for i in range(12)]			
		emp_cnt_total = sum(emp_cnt)
				
		hours_per_day = [float("{0:.0f}".format(a/b)) for a, b in zip(emp_hours, [31,28,31,30,31,30,31,31,30,31,30,31])]
		hours_per_day_avg = "{0:.2f}".format(sum(hours_per_day) / float(len([a for a in hours_per_day if a > 0]) or 1))
		
		cost_per_hour = [0 if b == 0 else float("{0:.0f}".format(a/b)) for a, b in zip(emp_cost, emp_hours)]
		cost_per_hour_avg = sum(cost_per_hour) / float(len([a for a in cost_per_hour if a > 0]) or 1)
				
		sql = """select * from hr_overtime_report_department_amount where department = %s """ % (userinfo.department_id.id,)
		cr.execute(sql)
		if cr.rowcount > 0:
			dept_cost = cr.fetchall()[0]
			dept_cost = [0 if v is None else float("{0:.0f}".format(v)) for v in dept_cost]
			dept_cost.pop(0)
		else:
			dept_cost = [0 for i in range(12)]					
				
		departmental = [0 if b == 0 else float("{0:.1f}".format(a/b*100)) for a, b in zip(emp_cost, dept_cost)]
		
		sql = """select sum(jan),sum(feb),sum(mar),sum(apr),sum(may),sum(jun),sum(jul),sum(aug),sum(sep),sum(oct),sum(nov),sum(dec) from hr_overtime_report_department_amount"""
		cr.execute(sql)
		total_cost = cr.fetchall()[0]
		total_cost = [0 if v is None else float("{0:.0f}".format(v)) for v in total_cost]
				
		
		overall = [0 if b == 0 else float("{0:.1f}".format(a/b*100)) for a, b in zip(emp_cost, total_cost)]
		
		#abc = Ranking
		
		sql = """select * from hr_overtime_report_employee_amount"""			
		cr.execute(sql)
		emp_test = cr.fetchall()
				
		
		emp_rank = []
		emp_test_list = list(zip(*emp_test))
		#for i in range(1,13):
		#	unranked = sorted([int(a) for a in emp_test_list[i] if a is not None],reverse=True)
		#	ranked = ranking.Ranking(unranked,start=1)
		#	rank = '0/0'
		#	
		#	if rank_cost[i-1]:
		#		rank = str(ranked.rank(int(rank_cost[i-1]))) + "/" + str(len(unranked))
		#	emp_rank.append(rank)
		
		sql = """select employee_id,sum(amount) from hr_overtime_report group by employee_id"""			
		cr.execute(sql)
		total_rank_cost = cr.fetchall()
		
		#unranked = sorted([int(a) for a in zip(*total_rank_cost)[1] if a is not None],reverse=True)
		#ranked = ranking.Ranking(unranked,start=1)
		overall_rank = '0/0'
		
		#if emp_rank_cost_total:
		#	overall_rank = str(ranked.rank(int(emp_rank_cost_total))) + "/" + str(len(unranked))
					
		data =  {
			'emp': {
				'empid' : userinfo.code,
			},
			'empinfo': {
				'english_name' : userinfo.english_name or '',
				'code' : userinfo.code or '',
				'designation' : userinfo.job_id and userinfo.job_id.name or '',
				'department' : userinfo.department_id and userinfo.department_id.name or '',
				'nationality' : userinfo.country_id and userinfo.country_id.name or '',
				'joining_date' : userinfo.joining_date or '',
				'duration' : userinfo.joining_date and compute_duration(userinfo.joining_date) or '-',
				'reporting' : userinfo.parent_id and str(userinfo.parent_id.sudo().code) + ' - ' + userinfo.parent_id.sudo().short_name or '',					
				'emp_hours' : emp_hours,
				'emp_hours_total' : emp_hours_total,
				'emp_cost' : emp_cost,
				'emp_cost_total' : emp_cost_total,
				'emp_cnt' : emp_cnt,
				'emp_cnt_total' : emp_cnt_total,
				'hours_per_day' : hours_per_day,
				'hours_per_day_avg' : hours_per_day_avg,
				'cost_per_hour': cost_per_hour,
				'cost_per_hour_avg': cost_per_hour_avg,
				'departmental': departmental,
				'overall': overall,
				'emp_rank': emp_rank,
				'overall_rank': overall_rank,
				'month2': ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec','Average'],
				'months': ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec','Total'],
			},			
		}
		
		return data
		
class AttendanceDashboard(http.Controller):

	@http.route('/attendance_dashboard/data', type='json', auth='user')
	def attendance_dashboard_data(self, userid=0):
		
		#if not request.env.user.has_group('base.group_erp_manager'):
		#	raise AccessError("Access Denied")
		
		cr = request.cr
		if userid == 0:
			userinfo = request.env['hr.employee'].search([('user_id','=',request.env.user.id)])
		else:	
			userinfo = request.env['hr.employee'].search([('code','=',str(userid).zfill(4))])
		
		if not userinfo:
			userinfo = request.env['hr.employee'].search([('user_id','=',request.env.user.id)])
			
		if not userinfo:	
			userinfo = request.env['hr.employee'].search([('code','=','0003')])
			
		attendance = [{'name':month,'days':[{'In':'.','Out':'.','Alert':'0','TT':'','Color':''} for x in range(1,32)],'P':0,'T':0,'L':0,'A':0,'V':0,'R':0,} 
			for month in ['January','February','March','April','May','June','July','August','September','October','November','December']]
	
		att_recs = request.env['hr.attendance'].search([('employee_id','=',userinfo.id),'|',('check_in','>=','2018-01-01'),('check_out','>=','2018-01-01')],order='check_in')
		for att in att_recs:
			dt = strToDatetime(att.check_in or att.check_out)
			month = int(dt.strftime('%m'))-1
			day = int(dt.strftime('%d'))-1
			
			attendance[month]['days'][day]['In'] = att.check_in and localDate(request,strToDatetime(att.check_in)).strftime('%H:%M') or '--'
			attendance[month]['days'][day]['Out'] = att.check_out and localDate(request,strToDatetime(att.check_out)).strftime('%H:%M') or '--'
									
			worked_hours_time = "--"
			if att.check_in and att.check_out:
				duration = datetime.strptime(att.check_out[:16],"%Y-%m-%d %H:%M")  - datetime.strptime(att.check_in[:16],"%Y-%m-%d %H:%M")  
				totsec = duration.total_seconds()
				h = totsec//3600
				m = (totsec%3600) // 60
				worked_hours_time =  "%02d:%02d" %(h,m)
	
	
			tooltip = "In Time :         " + (att.check_in and localDate(request,strToDatetime(att.check_in)).strftime('%Y-%m-%d %H:%M') or '--')
			tooltip = tooltip + "\nOut Time :     " + (att.check_out and localDate(request,strToDatetime(att.check_out)).strftime('%Y-%m-%d %H:%M') or '--')
			tooltip = tooltip + "\nWork Time : " + worked_hours_time
			
			
			attendance[month]['days'][day]['TT'] = tooltip
		
		leave_recs = request.env['hr.leave'].search([('employee_id','=',userinfo.id),('date_from','>=','2018-01-01')],order='date_from')
		emp_leave_total = 0
		for leave in leave_recs:	
			leave_days = abs(int(leave.number_of_days))
			for i in range(leave_days):				
				dt = strToDatetime(leave.date_from) + relativedelta(days=i)
				month = int(dt.strftime('%m'))-1
				day = int(dt.strftime('%d'))-1
			
				attendance[month]['days'][day]['In'] = leave.holiday_status_id.code
				attendance[month]['days'][day]['Color'] = leave.holiday_status_id.color_name
				attendance[month]['days'][day]['Out'] = 'L'
			
				tooltip = "Leave Type :         " + leave.holiday_status_id.name
				if leave.name:
					tooltip = tooltip + "\nDesc :     " + leave.name
				attendance[month]['days'][day]['TT'] = tooltip	
				
			attendance[month]['L'] += leave_days
			emp_leave_total += leave_days
			
		sql = """select * from hr_attendance_report_employee_present where employee = %s """ % (userinfo.id,)
		cr.execute(sql)
		
		if cr.rowcount > 0:
			emp_present = cr.fetchall()[0]
			emp_present = [0 if v is None else int(v) for v in emp_present]
			emp_present.pop(0)
		else:
			emp_present = [0 for i in range(12)]
			
		emp_present_total = sum(emp_present)
					
		for i in range(12):
			attendance[i]['P'] = emp_present[i]
		
			
		data =  {
			'emp': {
				'empid' : userinfo.code,				
			},
			'empinfo': {
				'english_name' : userinfo.english_name or '',
				'code' : userinfo.code or '',
				'designation' : userinfo.job_id and userinfo.job_id.name or '',
				'department' : userinfo.department_id and userinfo.department_id.name or '',
				'nationality' : userinfo.country_id and userinfo.country_id.name or '',
				'joining_date' : userinfo.joining_date or '',
				'duration' : userinfo.joining_date and compute_duration(userinfo.joining_date) or '-',
				'reporting' : userinfo.parent_id and str(userinfo.parent_id.sudo().code) + ' - ' + userinfo.parent_id.sudo().short_name or '',	
				
				'days': ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20', 						'21','22','23','24','25','26','27','28','29','30','31'],							
				'attendance' : attendance,
				
				'emp_present_total': emp_present_total, 
				'emp_leave_total': emp_leave_total,
			},			
		}
		
		return data
		
		
		
