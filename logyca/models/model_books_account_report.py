# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


import base64
import io
import requests
import PyPDF2
#Report Lab - https://www.reportlab.com/docs/reportlab-userguide.pdf
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

try: 
    from reportlab.lib.units import inch, cm
except ImportError:
    cm = None
    
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, SimpleDocTemplate, Table, TableStyle

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']

#---------------------------Modelo para generar LIBROS CONTABLES-------------------------------#

#---------------------------------- LIBRO DIARIO CONTABLE
class libro_diario_report(models.TransientModel):
    _name = 'logyca.libro_diario.report'
    _description = 'Reporte Libro Diario LOGYCA'
    
    company_id = fields.Many2one('res.company', string='Compañia', required=True)
    ano_filter = fields.Integer(string='Año', required=True)      
    month_filter = fields.Selection([
                                        ('1', 'Enero'),
                                        ('2', 'Febrero'),
                                        ('3', 'Marzo'),
                                        ('4', 'Abril'),
                                        ('5', 'Mayo'),
                                        ('6', 'Junio'),
                                        ('7', 'Julio'),
                                        ('8', 'Agosto'),
                                        ('9', 'Septiembre'),
                                        ('10', 'Octubre'),
                                        ('11', 'Noviembre'),
                                        ('12', 'Diciembre')        
                                    ], string='Mes', required=True)
    num_page_initial = fields.Integer(string='Último consecutivo paginación')
    pdf_file = fields.Binary('PDF file')
    pdf_file_name = fields.Char('PDF name', size=64)
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "LD {}-{} {} ".format(record.ano_filter,record.month_filter,record.company_id.name)))
        return result
    
    #Retonar columnas
    def get_columns(self):
        columns = 'CUENTA,,NOMBRE,SALDO INICIAL, DEBITOS, CREDITOS, SALDO FINAL'
        _columns = columns.split(",")
        return _columns
    
    #Ejecutar consulta SQL
    def run_sql(self):
        
        x_ano = self.ano_filter
        x_month = self.month_filter
        
        date_filter = str(x_ano)+'-'+str(x_month)+'-01'    
            
        if x_month == '12':
            x_ano = x_ano + 1 
            x_month = 1
        else:
            x_month = str(int(x_month) + 1)

        date_filter_next = str(x_ano)+'-'+str(x_month)+'-01'
        
        query_account_levelone = '''
            SELECT code_cuenta,'' as Code_Documento,name_cuenta,Sum(initial_balance) as initial_balance,Sum(debit) as debit,Sum(credit) as credit,Sum(new_balance) as new_balance 
            From (
            Select
                A.code,LevelAccount.LevelOne as Code_Cuenta,
                Case when LevelAccount.LevelOne = '1' then 'ACTIVO'
                     when LevelAccount.LevelOne = '2' then 'PASIVO'
                     when LevelAccount.LevelOne = '3' then 'PATRIMONIO'
                     when LevelAccount.LevelOne = '4' then 'INGRESOS'
                     when LevelAccount.LevelOne = '5' then 'GASTOS'
                     when LevelAccount.LevelOne = '6' then 'COSTO DE VENTAS'
                     when LevelAccount.LevelOne = '7' then 'COSTO DE PRODUCCION'
                     when LevelAccount.LevelOne = '8' then 'CUENTAS DE ORDEN DEUDORAS'
                     when LevelAccount.LevelOne = '9' then 'CUENTAS DE ORDEN ACREEDORAS'
                else '' end as Name_Cuenta,                
                COALESCE(D.saldo_ant,0) as initial_balance,
                SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
                SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
                COALESCE(D.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
                FROM (
                        select distinct substring(A.code_prefix for 1) as LevelOne
                        From account_group A
                        left join account_group b on a.id = b.parent_id
                        where (array_length(string_to_array(a.parent_path, '/'), 1) - 1)  = 1 and a.code_prefix is not null    
                ) as LevelAccount
                INNER JOIN account_account A on A.code like LevelAccount.LevelOne || '%s' 
                INNER JOIN account_move_line B on A.id = B.account_id 
                INNER JOIN account_move C on B.move_id = C.id and C.company_id = %s
                LEFT JOIN (
                            SELECT account_id,
                                    SUM(debit - credit) as saldo_ant 
                            FROM account_move_line
                            WHERE "date" < '%s' and parent_state = 'posted' group by account_id
                      ) as D on B.account_id = D.account_id
                WHERE  B.parent_state = 'posted' and B."date" < '%s' 
                GROUP by A.code,LevelAccount.LevelOne,D.saldo_ant
                ) as a
            Group by code_cuenta,name_cuenta
        ''' % (date_filter,date_filter,date_filter,date_filter,'%',self.company_id.id,date_filter,date_filter_next)
        
        query_account_leveltwo = '''
            SELECT code_cuenta,'' as Code_Documento,name_cuenta,Sum(initial_balance) as initial_balance,Sum(debit) as debit,Sum(credit) as credit,Sum(new_balance) as new_balance 
            From (
            Select
                A.code,LevelAccount.LevelTwo as Code_Cuenta,LevelAccount.LevelTwoName as Name_Cuenta,
                COALESCE(D.saldo_ant,0) as initial_balance,
                SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
                SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
                COALESCE(D.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
                FROM (
                        select distinct 
                                A.code_prefix as LevelTwo,A."name" as LevelTwoName					
                        From account_group A
                        left join account_group b on a.id = b.parent_id
                        where (array_length(string_to_array(a.parent_path, '/'), 1) - 1)  = 1 and a.code_prefix is not null    
                ) as LevelAccount
                INNER JOIN account_account A on A.code like LevelAccount.LevelTwo || '%s' 
                INNER JOIN account_move_line B on A.id = B.account_id 
                INNER JOIN account_move C on B.move_id = C.id and C.company_id = %s
                LEFT JOIN (
                            SELECT account_id,
                                    SUM(debit - credit) as saldo_ant 
                            FROM account_move_line
                            WHERE "date" < '%s' and parent_state = 'posted' group by account_id
                      ) as D on B.account_id = D.account_id
                WHERE  B.parent_state = 'posted' and B."date" < '%s' 
                GROUP by A.code,LevelAccount.LevelTwo,LevelAccount.LevelTwoName,D.saldo_ant
                ) as a
            Group by code_cuenta,name_cuenta
        ''' % (date_filter,date_filter,date_filter,date_filter,'%',self.company_id.id,date_filter,date_filter_next)
        
        query_account_levelthree = '''
            SELECT code_cuenta,'' as Code_Documento,name_cuenta,Sum(initial_balance) as initial_balance,Sum(debit) as debit,Sum(credit) as credit,Sum(new_balance) as new_balance 
            From (
            Select
                A.code,LevelAccount.LevelThree as Code_Cuenta,LevelAccount.LevelThreeName as Name_Cuenta,
                COALESCE(D.saldo_ant,0) as initial_balance,
                SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
                SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
                COALESCE(D.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
                FROM (
                        select distinct 
                                coalesce(B.code_prefix,'') as LevelThree,coalesce(B."name",'') as LevelThreeName
                        From account_group A
                        left join account_group b on a.id = b.parent_id
                        where (array_length(string_to_array(a.parent_path, '/'), 1) - 1)  = 1 and a.code_prefix is not null    
                ) as LevelAccount
                INNER JOIN account_account A on A.code like LevelAccount.LevelThree || '%s' 
                INNER JOIN account_move_line B on A.id = B.account_id 
                INNER JOIN account_move C on B.move_id = C.id and C.company_id = %s
                LEFT JOIN (
                            SELECT account_id,
                                    SUM(debit - credit) as saldo_ant 
                            FROM account_move_line
                            WHERE "date" < '%s' and parent_state = 'posted' group by account_id
                      ) as D on B.account_id = D.account_id
                WHERE  B.parent_state = 'posted' and B."date" < '%s' 
                GROUP by A.code,LevelAccount.LevelThree,LevelAccount.LevelThreeName,D.saldo_ant
                ) as a
            Where code_cuenta != ''
            Group by code_cuenta,name_cuenta
        ''' % (date_filter,date_filter,date_filter,date_filter,'%',self.company_id.id,date_filter,date_filter_next)
        
        query_account_levelfour = '''
            SELECT code_cuenta,'' as Code_Documento,name_cuenta,Sum(initial_balance) as initial_balance,Sum(debit) as debit,Sum(credit) as credit,Sum(new_balance) as new_balance 
            From (
            Select
                A.code,LevelAccount.LevelFour as Code_Cuenta,LevelAccount.LevelFourName as Name_Cuenta,
                COALESCE(D.saldo_ant,0) as initial_balance,
                SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
                SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
                COALESCE(D.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
                FROM (
                        select distinct 
                                coalesce(B.code_prefix,'') as LevelFour,coalesce(B."name",'') as LevelFourName
                        From account_group A
                        left join account_group b on a.id = b.parent_id
                        where (array_length(string_to_array(a.parent_path, '/'), 1) - 2)  = 1 and a.code_prefix is not null    
                ) as LevelAccount
                INNER JOIN account_account A on A.code like LevelAccount.LevelFour || '%s' 
                INNER JOIN account_move_line B on A.id = B.account_id 
                INNER JOIN account_move C on B.move_id = C.id and C.company_id = %s
                LEFT JOIN (
                            SELECT account_id,
                                    SUM(debit - credit) as saldo_ant 
                            FROM account_move_line
                            WHERE "date" < '%s' and parent_state = 'posted' group by account_id
                      ) as D on B.account_id = D.account_id
                WHERE  B.parent_state = 'posted' and B."date" < '%s' 
                GROUP by A.code,LevelAccount.LevelFour,LevelAccount.LevelFourName,D.saldo_ant
                ) as a
            Where code_cuenta != ''
            Group by code_cuenta,name_cuenta
        ''' % (date_filter,date_filter,date_filter,date_filter,'%',self.company_id.id,date_filter,date_filter_next)
        
        query_account = '''
            SELECT
            D.code as Code_Cuenta,'' as Code_Documento,D."name" as Name_Cuenta,
            COALESCE(E.saldo_ant,0) as initial_balance,
            SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
            SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
            COALESCE(E.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
            FROM account_move A 
            INNER JOIN account_move_line B on a.id = b.move_id
            INNER JOIN account_account D on B.account_id = D.id            
            LEFT JOIN (
                        SELECT account_id,
                                SUM(debit - credit) as saldo_ant 
                        FROM account_move_line 
                        WHERE "date" < '%s' and parent_state = 'posted' group by account_id
                  ) as E on b.account_id = E.account_id  
            WHERE  B.parent_state = 'posted' and a.company_id = %s and B."date" < '%s'
            GROUP by D.code,D."name",E.saldo_ant
        ''' % (date_filter,date_filter,date_filter,date_filter,date_filter,self.company_id.id,date_filter_next)
        
        query_journal = '''
            SELECT
            D.code as Code_Cuenta,--D."name" as Name_Cuenta,
            C.code as Code_Documento,C."name" as Name_Documento,
            COALESCE(E.saldo_ant,0) as initial_balance,
            SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
            SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
            COALESCE(E.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
            FROM account_move A 
            INNER JOIN account_move_line B on a.id = b.move_id
            INNER JOIN account_journal C on a.journal_id = C.id
            INNER JOIN account_account D on B.account_id = D.id            
            LEFT JOIN (
                        SELECT journal_id,account_id,
                                SUM(debit - credit) as saldo_ant 
                        FROM account_move_line 
                        WHERE "date" < '%s' and parent_state = 'posted' group by journal_id,account_id
                  ) as E on b.journal_id = E.journal_id and b.account_id = E.account_id      
            WHERE  B.parent_state = 'posted' and a.company_id = %s and B."date" < '%s'
            GROUP by D.code,D."name",C.code,C."name",E.saldo_ant            
        ''' % (date_filter,date_filter,date_filter,date_filter,date_filter,self.company_id.id,date_filter_next)
        
         #Consulta final
        query = '''
            Select code_cuenta,code_documento,name_cuenta,initial_balance,debit,credit,new_balance
            From
            (
                %s
                union
                %s
                union
                %s
                union
                %s
                union
                %s
                union
                %s
            ) As A
            Order By A.code_cuenta,A.code_documento
        ''' % (query_account_levelone,query_account_leveltwo,query_account_levelthree,query_account_levelfour,query_account,query_journal)
        
        #raise ValidationError(_(query))       
        
        self._cr.execute(query)
        _res = self._cr.dictfetchall()
        return _res
    
    
    
    def get_pdf(self):        
        
        filename= 'LD '+str(self.ano_filter)+'-'+str(self.month_filter)+' '+self.company_id.name+'.pdf'
        pdf = io.BytesIO()
        
        #Encabezado
        def header(canvas, doc):
            canvas.saveState()
            
            #Compañia
            P_one = Paragraph(self.company_id.name,styleN)
            w, h = P_one.wrap(doc.width, doc.topMargin)
            P_one.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
            
            #Nit Compañia
            P_two = Paragraph('NIT: '+self.company_id.vat,styleN)
            w, h = P_two.wrap(doc.width, doc.topMargin-15)
            P_two.drawOn(canvas, doc.leftMargin, doc.height + (doc.topMargin-15) - h)
            
            #Titulo
            P_title = Paragraph('LIBRO DIARIO',styleN)
            w, h = P_title.wrap(doc.width+200, doc.topMargin)
            P_title.drawOn(canvas, doc.leftMargin+200, doc.height + doc.topMargin - h)
            
            #Codigo
            P_code = Paragraph('Código: LDA02',styleN)
            w, h = P_code.wrap(doc.width+400, doc.topMargin)
            P_code.drawOn(canvas, doc.leftMargin+400, doc.height + doc.topMargin - h)
            
            #Pagina
            P_pag = Paragraph('Página: '+str(self.num_page_initial+canvas.getPageNumber()),styleN)
            w, h = P_pag.wrap(doc.width+400, doc.topMargin-15)
            P_pag.drawOn(canvas, doc.leftMargin+400, doc.height + (doc.topMargin-15) - h)
            
            #Fecha impresión
            date_today = fields.Date.context_today(self)
            P_date = Paragraph('Fecha impresión: '+str(date_today),styleN)
            w, h = P_date.wrap(doc.width, doc.topMargin-40)
            P_date.drawOn(canvas, doc.leftMargin, doc.height + (doc.topMargin-40) - h)
            
            #Fecha Informe
            P_dateimp = Paragraph('Fecha informe: '+str(self.ano_filter)+'-'+str(self.month_filter),styleN)
            w, h = P_dateimp.wrap(doc.width+200, doc.topMargin-40)
            P_dateimp.drawOn(canvas, doc.leftMargin+200, doc.height + (doc.topMargin-40) - h)
            
            canvas.restoreState()
            
        #doc = SimpleDocTemplate(pdf, pagesize=letter,rightMargin=72,leftMargin=72,topMargin=18,bottomMargin=18)
        doc = BaseDocTemplate(pdf, pagesize=letter,rightMargin=70,leftMargin=70,topMargin=20,bottomMargin=20)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height-2*cm,id='normal')
        template = PageTemplate(id='test', frames=frame, onPage=header)
        doc.addPageTemplates([template])
        elems = []

        #Tabla
        data = []
        #Encabezado Tabla
        result_columns = self.get_columns()
        data.append(result_columns)        
        #Agregar query        
        result_query = self.run_sql()
        #Detalle Tabla 
        account_code = ''
        for query in result_query:
            file = []
            num_row = 1            
            for row in query.values(): 
                if num_row == 1 and account_code == row:
                    file.append('')
                else:
                    if num_row > 3:
                        format_num = '{:,.2f}'.format(row)
                        file.append(format_num)                    
                    else:    
                        file.append(row)                    
                if num_row == 1:
                    account_code = row
                num_row = num_row + 1
            data.append(file)
            
        f = Table(data, repeatRows=1)
        
        styles = TableStyle([
            ('ALIGN',(0,0),(-1,-1),'RIGHT'),
            ('ALIGN',(0,0),(-5,-1),'LEFT'),
            ('FONTSIZE',(0,0),(-1,-1),7),
            ('FONTSIZE',(0,0),(6,0),8),
            ('TOPPADDING',(0,0),(-1,0),10),
            ('LINEABOVE', (0,0), (-1, 0), 2, colors.black),
        ])
        
        f.setStyle(styles)
        elems.append(f)
        doc.build(elems)
        
        #c = doc._makeCanvas(filename)
        
        #c.save()        
           
        self.write({
            'pdf_file': base64.encodestring(pdf.getvalue()),
            'pdf_file_name': filename,
        })
            
        action = {
                    'name': 'ReporteLibroDiario',
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=logyca.libro_diario.report&id=" + str(self.id) + "&filename_field=pdf_file_name&field=pdf_file&download=true&filename=" + self.pdf_file_name,
                    'target': 'self',
                }
        return action
        
#---------------------------------- LIBRO MAYOR
class libro_mayor_report(models.TransientModel):
    _name = 'logyca.libro_mayor.report'
    _description = 'Reporte Libro Mayor LOGYCA'
    
    company_id = fields.Many2one('res.company', string='Compañia', required=True)
    ano_filter = fields.Integer(string='Año', required=True)      
    month_filter = fields.Selection([
                                        ('1', 'Enero'),
                                        ('2', 'Febrero'),
                                        ('3', 'Marzo'),
                                        ('4', 'Abril'),
                                        ('5', 'Mayo'),
                                        ('6', 'Junio'),
                                        ('7', 'Julio'),
                                        ('8', 'Agosto'),
                                        ('9', 'Septiembre'),
                                        ('10', 'Octubre'),
                                        ('11', 'Noviembre'),
                                        ('12', 'Diciembre')        
                                    ], string='Mes', required=True)
    num_page_initial = fields.Integer(string='Último consecutivo paginación')
    pdf_file = fields.Binary('PDF file')
    pdf_file_name = fields.Char('PDF name', size=64)
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "LM {}-{} {} ".format(record.ano_filter,record.month_filter,record.company_id.name)))
        return result
    
    #Retonar columnas
    def get_columns(self):
        columns = 'CUENTA,NOMBRE,SALDO INICIAL, DEBITOS, CREDITOS, SALDO FINAL'
        _columns = columns.split(",")
        return _columns
    
    #Ejecutar consulta SQL
    def run_sql(self):
        
        x_ano = self.ano_filter
        x_month = self.month_filter
        
        date_filter = str(x_ano)+'-'+str(x_month)+'-01'

        if x_month == '1':
            x_ano_inic = x_ano + 1
            date_filter_inic = str(x_ano_inic)+'-01'+'-01'
        else:
            date_filter_inic = str(x_ano)+'-01'+'-01'
            
        if x_month == '12':
            x_ano = x_ano + 1 
            x_month = 1
        else:
            x_month = str(int(x_month) + 1)

        date_filter_next = str(x_ano)+'-'+str(x_month)+'-01'
        
        
        query_account_levelone = '''
            SELECT code_cuenta,name_cuenta,Sum(initial_balance) as initial_balance,Sum(debit) as debit,Sum(credit) as credit,Sum(new_balance) as new_balance 
            From (
            Select
                A.code,LevelAccount.LevelOne as Code_Cuenta,
                Case when LevelAccount.LevelOne = '1' then 'ACTIVO'
                     when LevelAccount.LevelOne = '2' then 'PASIVO'
                     when LevelAccount.LevelOne = '3' then 'PATRIMONIO'
                     when LevelAccount.LevelOne = '4' then 'INGRESOS'
                     when LevelAccount.LevelOne = '5' then 'GASTOS'
                     when LevelAccount.LevelOne = '6' then 'COSTO DE VENTAS'
                     when LevelAccount.LevelOne = '7' then 'COSTO DE PRODUCCION'
                     when LevelAccount.LevelOne = '8' then 'CUENTAS DE ORDEN DEUDORAS'
                     when LevelAccount.LevelOne = '9' then 'CUENTAS DE ORDEN ACREEDORAS'
                else '' end as Name_Cuenta,
                COALESCE(D.saldo_ant,0) as initial_balance,
                SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
                SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
                COALESCE(D.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
                FROM (
                        select distinct substring(A.code_prefix for 1) as LevelOne
                        From account_group A
                        left join account_group b on a.id = b.parent_id
                        where (array_length(string_to_array(a.parent_path, '/'), 1) - 1)  = 1 and a.code_prefix is not null    
                ) as LevelAccount
                INNER JOIN account_account A on A.code like LevelAccount.LevelOne || '%s' 
                INNER JOIN account_move_line B on A.id = B.account_id 
                INNER JOIN account_move C on B.move_id = C.id and C.company_id = %s


                LEFT JOIN (
                            SELECT account_id,
                                    SUM(debit - credit) as saldo_ant 
                            FROM account_move_line l
                            INNER JOIN account_account c on c.id=l.account_id
                            WHERE 
                                CASE
                                    WHEN user_type_id = 13 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 14 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 15 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 16 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 17 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 1 THEN "date" < '%s'
                                    WHEN user_type_id = 2 THEN "date" < '%s'
                                    WHEN user_type_id = 3 THEN "date" < '%s'
                                    WHEN user_type_id = 5 THEN "date" < '%s'
                                    WHEN user_type_id = 8 THEN "date" < '%s'
                                    WHEN user_type_id = 9 THEN "date" < '%s'
                                    WHEN user_type_id = 11 THEN "date" < '%s'
                                    ELSE "date" < '%s'
                                END
                            and parent_state = 'posted' group by account_id
                      ) as D on B.account_id = D.account_id
                WHERE  B.parent_state = 'posted' and B."date" < '%s' 
                GROUP by A.code,LevelAccount.LevelOne,D.saldo_ant
                ) as a
            Group by code_cuenta,name_cuenta
        ''' % (date_filter,date_filter,date_filter,date_filter,'%',self.company_id.id,
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,date_filter_next)

        query_account_leveltwo = '''
            SELECT code_cuenta,name_cuenta,Sum(initial_balance) as initial_balance,Sum(debit) as debit,Sum(credit) as credit,Sum(new_balance) as new_balance 
            From (
            Select
                A.code,LevelAccount.LevelTwo as Code_Cuenta,LevelAccount.LevelTwoName as Name_Cuenta,
                COALESCE(D.saldo_ant,0) as initial_balance,
                SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
                SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
                COALESCE(D.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
                FROM (
                        select distinct 
                                A.code_prefix as LevelTwo,A."name" as LevelTwoName					
                        From account_group A
                        left join account_group b on a.id = b.parent_id
                        where (array_length(string_to_array(a.parent_path, '/'), 1) - 1)  = 1 and a.code_prefix is not null    
                ) as LevelAccount
                INNER JOIN account_account A on A.code like LevelAccount.LevelTwo || '%s' 
                INNER JOIN account_move_line B on A.id = B.account_id 
                INNER JOIN account_move C on B.move_id = C.id and C.company_id = %s
                LEFT JOIN (
                            SELECT account_id,
                                    SUM(debit - credit) as saldo_ant 
                            FROM account_move_line l
                            INNER JOIN account_account c on c.id=l.account_id
                            WHERE 
                                CASE
                                    WHEN user_type_id = 13 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 14 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 15 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 16 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 17 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 1 THEN "date" < '%s'
                                    WHEN user_type_id = 2 THEN "date" < '%s'
                                    WHEN user_type_id = 3 THEN "date" < '%s'
                                    WHEN user_type_id = 5 THEN "date" < '%s'
                                    WHEN user_type_id = 8 THEN "date" < '%s'
                                    WHEN user_type_id = 9 THEN "date" < '%s'
                                    WHEN user_type_id = 11 THEN "date" < '%s'
                                    ELSE "date" < '%s'
                                END
                            and parent_state = 'posted' group by account_id
                      ) as D on B.account_id = D.account_id
                WHERE  B.parent_state = 'posted' and B."date" < '%s' 
                GROUP by A.code,LevelAccount.LevelTwo,LevelAccount.LevelTwoName,D.saldo_ant
                ) as a
            Group by code_cuenta,name_cuenta
        ''' % (date_filter,date_filter,date_filter,date_filter,'%',self.company_id.id,
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,            
                date_filter,date_filter_next)
        
        query_account_levelthree = '''
            SELECT code_cuenta,name_cuenta,Sum(initial_balance) as initial_balance,Sum(debit) as debit,Sum(credit) as credit,Sum(new_balance) as new_balance 
            From (
            Select
                A.code,LevelAccount.LevelThree as Code_Cuenta,LevelAccount.LevelThreeName as Name_Cuenta,
                COALESCE(D.saldo_ant,0) as initial_balance,
                SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
                SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
                COALESCE(D.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
                FROM (
                        select distinct 
                                coalesce(B.code_prefix,'') as LevelThree,coalesce(B."name",'') as LevelThreeName
                        From account_group A
                        left join account_group b on a.id = b.parent_id
                        where (array_length(string_to_array(a.parent_path, '/'), 1) - 1)  = 1 and a.code_prefix is not null    
                ) as LevelAccount
                INNER JOIN account_account A on A.code like LevelAccount.LevelThree || '%s' 
                INNER JOIN account_move_line B on A.id = B.account_id 
                INNER JOIN account_move C on B.move_id = C.id and C.company_id = %s
                LEFT JOIN (
                            SELECT account_id,
                                    SUM(debit - credit) as saldo_ant 
                            FROM account_move_line l
                            INNER JOIN account_account c on c.id=l.account_id
                            WHERE 
                                CASE
                                    WHEN user_type_id = 13 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 14 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 15 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 16 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 17 THEN "date" >= '%s' and "date" < '%s'
                                    WHEN user_type_id = 1 THEN "date" < '%s'
                                    WHEN user_type_id = 2 THEN "date" < '%s'
                                    WHEN user_type_id = 3 THEN "date" < '%s'
                                    WHEN user_type_id = 5 THEN "date" < '%s'
                                    WHEN user_type_id = 8 THEN "date" < '%s'
                                    WHEN user_type_id = 9 THEN "date" < '%s'
                                    WHEN user_type_id = 11 THEN "date" < '%s'
                                    ELSE "date" < '%s'
                                END
                            and parent_state = 'posted' group by account_id
                      ) as D on B.account_id = D.account_id
                WHERE  B.parent_state = 'posted' and B."date" < '%s' 
                GROUP by A.code,LevelAccount.LevelThree,LevelAccount.LevelThreeName,D.saldo_ant
                ) as a
            Where code_cuenta != ''
            Group by code_cuenta,name_cuenta
        ''' % (date_filter,date_filter,date_filter,date_filter,'%',self.company_id.id,
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter, 
                date_filter_inic, date_filter, 
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,
                date_filter,date_filter_next)
        
         #Consulta final
        query = '''
            Select code_cuenta,name_cuenta,initial_balance,debit,credit,new_balance 
            From
            (
                %s
                union
                %s
                union
                %s
            ) As A
            Order By Code_Cuenta
        ''' % (query_account_levelone,query_account_leveltwo,query_account_levelthree)
        
        #raise ValidationError(_(query))
        self._cr.execute(query)
        _res = self._cr.dictfetchall()
        return _res
    
    
    
    def get_pdf(self):        
        
        filename= 'LM '+str(self.ano_filter)+'-'+str(self.month_filter)+' '+self.company_id.name+'.pdf'
        pdf = io.BytesIO()
        
        #Encabezado
        def header(canvas, doc):
            canvas.saveState()
            
            #Compañia
            P_one = Paragraph(self.company_id.name,styleN)
            w, h = P_one.wrap(doc.width, doc.topMargin)
            P_one.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
            
            #Nit Compañia
            P_two = Paragraph('NIT: '+self.company_id.vat,styleN)
            w, h = P_two.wrap(doc.width, doc.topMargin-15)
            P_two.drawOn(canvas, doc.leftMargin, doc.height + (doc.topMargin-15) - h)
            
            #Titulo
            P_title = Paragraph('LIBRO MAYOR',styleN)
            w, h = P_title.wrap(doc.width+200, doc.topMargin)
            P_title.drawOn(canvas, doc.leftMargin+200, doc.height + doc.topMargin - h)
            
            #Codigo
            P_code = Paragraph('Código: LMO',styleN)
            w, h = P_code.wrap(doc.width+400, doc.topMargin)
            P_code.drawOn(canvas, doc.leftMargin+400, doc.height + doc.topMargin - h)
            
            #Pagina
            P_pag = Paragraph('Página: '+str(self.num_page_initial+canvas.getPageNumber()),styleN)
            w, h = P_pag.wrap(doc.width+400, doc.topMargin-15)
            P_pag.drawOn(canvas, doc.leftMargin+400, doc.height + (doc.topMargin-15) - h)
            
            #Fecha impresión
            date_today = fields.Date.context_today(self)
            P_date = Paragraph('Fecha impresión: '+str(date_today),styleN)
            w, h = P_date.wrap(doc.width, doc.topMargin-40)
            P_date.drawOn(canvas, doc.leftMargin, doc.height + (doc.topMargin-40) - h)
            
            #Fecha Informe
            P_dateimp = Paragraph('Fecha informe: '+str(self.ano_filter)+'-'+str(self.month_filter),styleN)
            w, h = P_dateimp.wrap(doc.width+200, doc.topMargin-40)
            P_dateimp.drawOn(canvas, doc.leftMargin+200, doc.height + (doc.topMargin-40) - h)
            
            canvas.restoreState()
            
        #doc = SimpleDocTemplate(pdf, pagesize=letter,rightMargin=72,leftMargin=72,topMargin=18,bottomMargin=18)
        doc = BaseDocTemplate(pdf, pagesize=letter,rightMargin=70,leftMargin=70,topMargin=20,bottomMargin=20)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height-2*cm,id='normal')
        template = PageTemplate(id='test', frames=frame, onPage=header)
        doc.addPageTemplates([template])
        elems = []

        #Tabla
        data = []
        #Encabezado Tabla
        result_columns = self.get_columns()
        data.append(result_columns)        
        #Agregar query        
        result_query = self.run_sql()
        #Detalle Tabla 
        account_code = ''
        for query in result_query:
            file = []
            line_blank = []
            num_row = 1            
            for row in query.values(): 
                if num_row == 1 and account_code != row[0:2]:
                    line_blank.append('')
                if num_row > 2:
                    format_num = '{:,.2f}'.format(row)
                    file.append(format_num)                    
                else:    
                    if num_row == 1 and len(row) == 1:
                        file.append(row)
                    if num_row == 1 and len(row) == 2:
                        file.append('     '+row)
                    if num_row == 1 and len(row) > 2:
                        file.append('        '+row)
                    if num_row != 1:
                        file.append(row)                    
                if num_row == 1:
                    account_code = row[0:2]                    
                num_row = num_row + 1
                
            if len(line_blank) > 0:
                data.append(line_blank)
            data.append(file)
            
        f = Table(data, repeatRows=1)
        
        styles = TableStyle([
            ('ALIGN',(0,0),(-1,-1),'RIGHT'),
            ('ALIGN',(0,0),(-5,-1),'LEFT'),
            ('FONTSIZE',(0,0),(-1,-1),7),
            ('FONTSIZE',(0,0),(5,0),8),
            ('TOPPADDING',(0,0),(-1,0),10),
            ('LINEABOVE', (0,0), (-1, 0), 2, colors.black),
        ])
        
        f.setStyle(styles)
        elems.append(f)
        doc.build(elems)
        
        #c = doc._makeCanvas(filename)
        
        #c.save()        
           
        self.write({
            'pdf_file': base64.encodestring(pdf.getvalue()),
            'pdf_file_name': filename,
        })
            
        action = {
                    'name': 'ReporteLibroMayor',
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=logyca.libro_mayor.report&id=" + str(self.id) + "&filename_field=pdf_file_name&field=pdf_file&download=true&filename=" + self.pdf_file_name,
                    'target': 'self',
                }
        return action
