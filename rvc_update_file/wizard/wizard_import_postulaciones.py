# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import xlrd
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class WizardImportPostulaciones(models.TransientModel):
    _name = 'wizard.import.postulaciones'
    _description = 'Asistente para Importar Postulaciones desde Excel'

    archivo_excel = fields.Binary(
        string='Archivo Excel',
        required=True,
        help='Suba el archivo Excel con las postulaciones a importar'
    )
    nombre_archivo = fields.Char(string='Nombre del Archivo')
    
    # Configuración del beneficio
    programa_id = fields.Many2one(
        'product.rvc',  # Ajustar según tu modelo
        string='Programa',
        default=lambda self: self._get_programa_logyca(),
        help='Programa LOGYCA / COLABORA'
    )
    
    resultado_importacion = fields.Text(
        string='Resultado de la Importación',
        readonly=True
    )

    def _get_programa_logyca(self):
        """Obtener el programa LOGYCA/COLABORA por defecto"""
        programa = self.env['product.rvc'].search([
            ('benefit_type', '=', 'colabora')], limit=1)
        return programa.id if programa else False

    def _validar_estructura_excel(self, sheet):
        """Valida que el Excel tenga las columnas requeridas"""
        columnas_requeridas = [
            'NIT',
            'RAZÓN SOCIAL DE LA EMPRESA',
            'NIVEL',
            'FECHA DE ACTIVACIÓN',
            'NOMBRE DEL CONTACTO',
            'CORREO DE ACTIVACIÓN',
            'TELEFONO DE CONTACTO',
            'SECTOR',
            'NIT EMPRESA HALONADORA',
        ]
        
        # Leer la primera fila (encabezados)
        encabezados = [sheet.cell_value(0, col) for col in range(sheet.ncols)]
        
        for columna in columnas_requeridas:
            if columna not in encabezados:
                raise ValidationError(
                    f"La columna '{columna}' no se encuentra en el archivo Excel.\n"
                    f"Columnas encontradas: {', '.join(encabezados)}"
                )
        
        return {columna: encabezados.index(columna) for columna in columnas_requeridas}

    def _limpiar_nit(self, nit):
        """Limpia el NIT removiendo caracteres especiales"""
        if not nit:
            return ''
        return str(nit).replace('-', '').replace('.', '').strip()

    def _crear_o_actualizar_partner(self, nit, razon_social, nombre_contacto, correo, phone, macro_sector):
        """Crea o actualiza el res.partner (tercero)"""
        Partner = self.env['res.partner']
        
        nit_limpio = self._limpiar_nit(nit)
        
        # Buscar si ya existe el partner por NIT
        partner = Partner.search([('vat', '=', nit_limpio), ('parent_id', '=', None)], limit=1)

        city_id = self.env['res.city'].search([('zipcode', '=', '11001')], limit=1)
        # Buscar el tipo de tercero donde types = '1'
        tipo_tercero = self.env['logyca.type_thirdparty'].search([('types', '=', '1')], limit=1)
        if not tipo_tercero:
            raise ValidationError(
                "No se encontró el tipo de tercero con types='1'. "
                "Por favor, verifique la configuración de tipos de tercero."
            )
        
        if macro_sector=='Comercio':
            macro_sector='comercio'
        elif macro_sector=='Manufactura':
            macro_sector='manufactura'
        else:
            macro_sector='servicios'
        
        vals = {
            'name': razon_social,
            'vat': nit_limpio,
            'company_type': 'company',
            'email': correo,
            'phone': phone,
            'mobile': phone,
            'is_company': True,
            'country_id': self.env.ref('base.co').id,  # Colombia
            'city_id': city_id.id,
            'state_id': city_id.state_id.id,  # Colombia
            'x_type_thirdparty': [(6, 0, [tipo_tercero.id])],
            'macro_sector': macro_sector,
        }
        if partner:
            _logger.info(f"Partner actualizado: {razon_social} (NIT: {nit_limpio})")
        else:
            partner = Partner.create(vals)
            _logger.info(f"Partner creado: {razon_social} (NIT: {nit_limpio})")
            # Crear o actualizar contacto
            if nombre_contacto and correo:
                contacto = Partner.search([
                    ('parent_id', '=', partner.id),
                    ('email', '=', correo)
                ], limit=1)
                
                contacto_vals = {
                    'name': nombre_contacto,
                    'email': correo,
                    'parent_id': partner.id,
                    'type': 'contact',
                    'company_type': 'person',
                }
                
                if contacto:
                    contacto.write(contacto_vals)
                else:
                    Partner.create(contacto_vals)
        
        return partner

    def _crear_beneficiario(self, partner, nivel):
        """Crea el registro de beneficiario si no existe"""
        Beneficiario = self.env['rvc.beneficiary']  # Ajustar según tu modelo
        contact_obj = self.env['res.partner']  # Ajustar según tu modelo
        
        beneficiario = Beneficiario.search([
            ('partner_id', '=', partner.id)
        ], limit=1)

        contact_id = contact_obj.search([
            ('parent_id', '=', partner.id)
        ], limit=1)

        if not beneficiario:
            beneficiario = Beneficiario.create({
                'partner_id': partner.id,
                'contact_id': contact_id.id,
                'active': True,
                'contact_name': contact_id.name,
                'contact_phone': partner.phone,
                'contact_email': partner.email,
                'contact_position': 'RVC',
                'active': True,
            })
            _logger.info(f"Beneficiario creado para: {partner.name}")
        
        return beneficiario

    def _crear_sponsor(self, halonador_id, halonador_vat):
        halonador = self.env['rvc.sponsor']  # Ajustar según tu modelo        
        halonador_rvc = halonador.search([
            ('vat', '=', halonador_vat)
        ], limit=1)
        if not halonador_rvc:
            halonador_rvc = halonador.search([
                ('partner_id', '=', halonador_id.id)
            ], limit=1)

        if not halonador_rvc:
            halonador_rvc = halonador.create({
                'partner_id': halonador_id.id,
                'active': True,
            })
            _logger.info(f"Halonador creado para: {halonador_id.name}")
        return halonador_rvc

    def _parsear_fecha(self, fecha_valor):
        """Convierte diferentes formatos de fecha a date de Odoo"""
        if isinstance(fecha_valor, float):
            # Fecha en formato numérico de Excel
            fecha = xlrd.xldate_as_datetime(fecha_valor, 0)
            return fecha.date()
        elif isinstance(fecha_valor, str):
            # Intentar diferentes formatos de fecha
            formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']
            for formato in formatos:
                try:
                    return datetime.strptime(fecha_valor, formato).date()
                except ValueError:
                    continue
            raise ValidationError(f"Formato de fecha no válido: {fecha_valor}")
        return False

    def _crear_postulacion(self, partner, beneficiario, fecha_activacion, correo, nivel, sponsor):
        """Crea la postulación en estado aceptado"""
        Postulacion = self.env['benefit.application']  # Ajustar según tu modelo
        
        # Verificar si ya existe una postulación
        postulacion = Postulacion.search([
            ('partner_id', '=', beneficiario.id),
            ('product_id', '=', self.programa_id.id),
            ('colabora_level', '=', nivel),
            ('state', '=', 'confirm')
        ], limit=1)

        if postulacion:
            _logger.warning(f"Ya existe una postulación aceptada para: {partner.name}")
            return postulacion
        
        fecha_activacion_date = self._parsear_fecha(fecha_activacion)
        postulacion = Postulacion.create({
            'partner_id': beneficiario.id,
            'product_id': self.programa_id.id,
            'parent_id': sponsor.id,
            'end_date_colabora': fecha_activacion_date,
            'email_colabora': correo,
            'colabora_level': nivel,
            'state': 'confirm',
        })
        _logger.info(f"Postulación creada para: {partner.name}")
        return postulacion

    def action_importar(self):
        """Procesa el archivo Excel e importa las postulaciones"""
        self.ensure_one()
        
        if not self.archivo_excel:
            raise UserError("Debe cargar un archivo Excel")
        
        try:
            # Decodificar el archivo
            archivo_data = base64.b64decode(self.archivo_excel)
            book = xlrd.open_workbook(file_contents=archivo_data)
            sheet = book.sheet_by_index(0)
            
            # Validar estructura
            indices = self._validar_estructura_excel(sheet)
            
            # Contadores
            exitosos = 0
            errores = []
            
            # Procesar cada fila (empezando desde la fila 1, saltando encabezados)
            for row_idx in range(1, sheet.nrows):
                try:
                    # Leer datos de la fila
                    nit = str(sheet.cell_value(row_idx, indices['NIT']))
                    razon_social = sheet.cell_value(row_idx, indices['RAZÓN SOCIAL DE LA EMPRESA'])
                    nivel = str(sheet.cell_value(row_idx, indices['NIVEL']))
                    fecha_activacion = sheet.cell_value(row_idx, indices['FECHA DE ACTIVACIÓN'])
                    nombre_contacto = sheet.cell_value(row_idx, indices['NOMBRE DEL CONTACTO'])
                    correo = sheet.cell_value(row_idx, indices['CORREO DE ACTIVACIÓN'])
                    phone = sheet.cell_value(row_idx, indices['TELEFONO DE CONTACTO'])
                    macro_sector = sheet.cell_value(row_idx, indices['SECTOR'])
                    halonador = str(sheet.cell_value(row_idx, indices['NIT EMPRESA HALONADORA']))

                    # Validaciones básicas
                    if not nit or not razon_social:
                        errores.append(f"Fila {row_idx + 1}: NIT o Razón Social vacíos")
                        continue

                    suffix = ".0"
                    if nit.endswith(suffix):
                        nit = nit[:-len(suffix)]
                    if nivel.endswith(suffix):
                        nivel = nivel[:-len(suffix)]
                    if halonador.endswith(suffix):
                        halonador = halonador[:-len(suffix)]

                    # 1. Crear/actualizar partner
                    partner = self._crear_o_actualizar_partner(
                        nit, razon_social, nombre_contacto, correo, phone, macro_sector
                    )

                    halonador_obj = self.env['res.partner']  # Ajustar según tu modelo
                    halonador_id = halonador_obj.search([
                        ('vat', '=', halonador),
                        ('parent_id', '=', None)
                    ], limit=1)

                    # 2. Crear Halonador
                    sponsor = self._crear_sponsor(halonador_id, halonador)
                    # 2. Crear beneficiario
                    beneficiario = self._crear_beneficiario(partner, nivel)
                    # 3. Crear postulación
                    self._crear_postulacion(
                        partner, beneficiario, fecha_activacion, correo, nivel, sponsor
                    )
                    
                    exitosos += 1
                    
                except Exception as e:
                    error_msg = f"Fila {row_idx + 1} ({razon_social if 'razon_social' in locals() else 'N/A'}): {str(e)}"
                    errores.append(error_msg)
                    _logger.error(error_msg)
            
            # Preparar resultado
            resultado = f"✓ Importación completada\n\n"
            resultado += f"Registros exitosos: {exitosos}\n"
            resultado += f"Registros con errores: {len(errores)}\n\n"
            
            if errores:
                resultado += "ERRORES:\n" + "\n".join(errores)
            
            self.resultado_importacion = resultado
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.import.postulaciones',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'context': {'show_result': True}
            }
            
        except Exception as e:
            raise UserError(f"Error al procesar el archivo: {str(e)}")

    def action_cerrar(self):
        """Cierra el wizard"""
        return {'type': 'ir.actions.act_window_close'}
