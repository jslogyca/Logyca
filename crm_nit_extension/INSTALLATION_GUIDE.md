# Guía de Instalación y Prueba - CRM NIT Extension

## 📋 Requisitos Previos
- Odoo 17 instalado y funcionando
- Módulo CRM nativo instalado
- Acceso a la carpeta de addons de Odoo
- Permisos de administrador en Odoo

## 🚀 Instalación

### Paso 1: Copiar el Módulo
```bash
# Copiar el módulo a la carpeta de addons
cp -r crm_nit_extension /ruta/a/odoo/addons/

# O crear enlace simbólico
ln -s /ruta/completa/crm_nit_extension /ruta/a/odoo/addons/
```

### Paso 2: Dar Permisos
```bash
# Asegurar que Odoo pueda leer el módulo
chmod -R 755 /ruta/a/odoo/addons/crm_nit_extension
chown -R odoo:odoo /ruta/a/odoo/addons/crm_nit_extension
```

### Paso 3: Actualizar Lista de Aplicaciones
1. Iniciar sesión en Odoo como administrador
2. Ir a **Apps** (Aplicaciones)
3. Hacer clic en el menú de tres puntos ⋮
4. Seleccionar **Update Apps List** (Actualizar Lista de Aplicaciones)
5. En el diálogo, hacer clic en **Update** (Actualizar)

### Paso 4: Buscar e Instalar
1. En la búsqueda de Apps, escribir: `CRM NIT Extension`
2. Hacer clic en el módulo cuando aparezca
3. Hacer clic en **Install** (Instalar)
4. Esperar a que termine la instalación

## ✅ Verificación de Instalación

### Verificar en la Base de Datos
```sql
-- Verificar que el campo fue creado
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'crm_lead' 
AND column_name = 'nit';

-- Debe retornar:
-- column_name | data_type
-- nit         | character varying
```

### Verificar en la Interfaz
1. Ir a **CRM > Leads**
2. Crear un nuevo Lead
3. Verificar que el campo **NIT** aparece después del campo "Nombre de la empresa"
4. El campo debe ser visible
5. Ingresar un valor de prueba (ej: 900123456-7)
6. Guardar el registro

## 🧪 Pruebas Funcionales

### Prueba 1: Visibilidad en Lead
```
Estado: type = 'lead'
Resultado Esperado: Campo NIT es VISIBLE
```
**Pasos:**
1. Crear nuevo Lead
2. Verificar que campo NIT está visible
3. ✅ Campo debe aparecer y ser editable

### Prueba 2: Invisibilidad en Opportunity
```
Estado: type = 'opportunity'
Resultado Esperado: Campo NIT es INVISIBLE
```
**Pasos:**
1. Crear nuevo Lead
2. Convertir a Oportunidad usando botón "Convert to Opportunity"
3. Abrir la Oportunidad creada
4. ✅ Campo NIT NO debe ser visible

### Prueba 3: Tracking de Cambios
```
Funcionalidad: Seguimiento de cambios
Resultado Esperado: Los cambios se registran en el chatter
```
**Pasos:**
1. Crear Lead con NIT: "900123456-7"
2. Guardar
3. Editar y cambiar NIT a: "800987654-3"
4. Guardar
5. ✅ En el chatter debe aparecer el registro del cambio

### Prueba 4: Registro Nuevo (type = False)
```
Estado: type = False (nuevo registro)
Resultado Esperado: Campo NIT es VISIBLE
```
**Pasos:**
1. Abrir formulario de nuevo Lead (antes de guardar)
2. ✅ Campo NIT debe ser visible desde el inicio

## 🔍 Solución de Problemas

### Problema: El módulo no aparece en Apps
**Solución:**
```bash
# Reiniciar el servicio de Odoo
sudo systemctl restart odoo

# O si usas el comando directo
./odoo-bin --addons-path=/ruta/a/addons -d nombre_db -u all

# Verificar logs
tail -f /var/log/odoo/odoo.log
```

### Problema: El campo no aparece en el formulario
**Verificar:**
1. Que la vista se heredó correctamente:
   ```
   Ir a: Settings > Technical > User Interface > Views
   Buscar: crm.lead.form.inherit.nit
   ```
2. Que el módulo está instalado:
   ```
   Ir a: Apps
   Buscar: CRM NIT Extension
   Estado: Debe aparecer "Installed"
   ```

### Problema: Error al instalar
**Revisar logs:**
```bash
tail -n 100 /var/log/odoo/odoo.log | grep -i error
```

**Errores comunes:**
- **ParseError**: Revisar sintaxis XML en `views/crm_lead_views.xml`
- **ImportError**: Verificar que todos los archivos `__init__.py` existen
- **AccessError**: Verificar permisos de archivos

## 📊 Estructura del Módulo

```
crm_nit_extension/
├── __init__.py                          # Inicialización del módulo
├── __manifest__.py                      # Manifiesto con metadatos
├── README.md                            # Documentación principal
├── models/
│   ├── __init__.py                      # Importa los modelos
│   └── crm_lead.py                      # Herencia de crm.lead + campo NIT
├── views/
│   └── crm_lead_views.xml              # Vista heredada del formulario
├── security/                            # (Vacío - sin reglas adicionales)
└── static/
    └── description/
        └── index.html                   # Descripción para el App Store
```

## 📝 Comandos Útiles

### Actualizar el módulo después de cambios
```bash
# En línea de comandos
./odoo-bin -d nombre_db -u crm_nit_extension

# O desde la interfaz
Apps > CRM NIT Extension > Upgrade
```

### Desinstalar el módulo
```bash
# Desde la interfaz
Apps > CRM NIT Extension > Uninstall

# El campo permanecerá en la BD pero no será visible
```

### Ver información del módulo
```python
# En Python shell de Odoo
module = env['ir.module.module'].search([('name', '=', 'crm_nit_extension')])
print(f"Estado: {module.state}")
print(f"Versión: {module.latest_version}")
```

## 🎯 Checklist de Verificación

- [ ] Módulo copiado a carpeta addons
- [ ] Lista de aplicaciones actualizada
- [ ] Módulo instalado exitosamente
- [ ] Campo NIT visible en Lead
- [ ] Campo NIT invisible en Opportunity
- [ ] Campo NIT invisible en registro nuevo (antes de guardar debe ser visible)
- [ ] Tracking de cambios funcionando
- [ ] Valores se guardan correctamente
- [ ] Sin errores en logs de Odoo

## 📞 Contacto y Soporte

**Desarrollador:** LOGYCA  
**Website:** https://www.logyca.com  
**Versión del Módulo:** 17.0.1.0.0  
**Versión de Odoo:** 17.0

---
*Última actualización: Diciembre 2024*
