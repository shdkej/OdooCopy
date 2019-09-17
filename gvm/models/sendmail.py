# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
import os

class gvm_mail():
  def gvm_send_mail(self, uname, receiver, post, postId, po_num, model_name, menu_id, action_id):
     sender = 'nohsh@gvmltd.com'
     receivers = []
     name = str(uname)
     url = "https://erp.gvmltd.com/"
     subject = "[GVM]["+str(po_num)+"]"+ name + " 님이 "+ post +" 를 올렸습니다."
     url = "https://erp.gvmltd.com/"

     real_server = os.getenv('GVM_ERP')
     if real_server == 'True':#True
       if receiver:
         for rc in receiver:
           receivers.append(str(rc.work_email))
     else:#Blank
       subject = '[TEST]' + subject
       url = "http://192.168.0.3/"
       
     receivers.append('nohsh@gvmltd.com')

     post_id = str(postId)
     html = str('<a href="' + url + 
       'web#view_type=form&model=' + model_name + '&menu_id=' + menu_id + 
       '&id=' + post_id + '&action=' + action_id +
       '" style="padding: 5px 10px; font-size: 12px; line-height: 18px; color: #FFFFFF; border-color:#875A7B; text-decoration: none; display: inline-block; margin-bottom: 0px; font-weight: 400; text-align: center; vertical-align: middle; cursor: pointer; white-space: nowrap; background-image: none; background-color: #875A7B; border: 1px solid #875A7B; border-radius:3px">바로가기</a>')

     msg = MIMEText(html, 'html', _charset='utf-8')
     msg['subject'] = subject
     msg['from'] = 'GVM_ERP'

     s = smtplib.SMTP_SSL(host='smtp.mailplug.co.kr', port=465)
     s.login(user='nohsh@gvmltd.com', password='@shtjdgh412')
     s.sendmail(sender, receivers, msg.as_string())
     s.quit()
