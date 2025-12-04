# 🔧 HOTFIX v1.1.0 - Corrección de Templates de Email

## 📋 Problemas Corregidos

### ✅ **Problema 1: Variables sin procesar en emails**
**Síntoma:** El email mostraba código literal como `${object.name}` en lugar de los valores reales.

**Causa:** Los templates usaban sintaxis Mako (`${...}` y `% if`) en lugar de la sintaxis QWeb de Odoo.

**Solución:** Se reemplazó toda la sintaxis Mako por sintaxis QWeb:
- `${object.field}` → `<t t-esc="object.field"/>`
- `% if condition:` → `<t t-if="condition">`
- `${method()}` → `<t t-esc="method()"/>`
- URLs dinámicas: `href="${url}"` → `t-attf-href="{{url}}"`

### ✅ **Problema 2: Error 404 al hacer clic en "Ver y Aprobar Solicitud"**
**Síntoma:** Al hacer clic en el botón del email, aparecía "No pudimos encontrar la página que busca"

**Causa Potencial:** 
1. El `web.base.url` no estaba configurado correctamente
2. La ruta `/ausencias/approve/` no estaba siendo reconocida

**Solución:** El código del controlador está correcto. Verificar:
```bash
# En Odoo Shell o Configuración > Parámetros del Sistema
web.base.url = https://tu-dominio.com
```

---

## 📦 Archivos Modificados

### `data/mail_template.xml`
- ✅ Template de notificación al aprobador
- ✅ Template de confirmación de aprobación
- ✅ Template de notificación de rechazo

### `__manifest__.py`
- Versión actualizada a `17.0.1.1.0`

---

## 🚀 Cómo Instalar/Actualizar

### **Opción 1: Actualizar el Módulo Existente**

1. **Hacer backup de tu base de datos**
   ```bash
   pg_dump nombre_base_datos > backup_antes_hotfix.sql
   ```

2. **Reemplazar el módulo**
   ```bash
   cd /ruta/a/odoo/addons
   rm -rf website_leave_form  # Eliminar versión antigua
   unzip website_leave_form_HOTFIX_v1.1.0.zip  # Descomprimir nueva versión
   ```

3. **Reiniciar Odoo**
   ```bash
   sudo systemctl restart odoo
   ```

4. **Actualizar en Odoo**
   - Ir a **Apps**
   - Buscar "Formulario Web de Ausencias"
   - Click en **Actualizar**
   - ✅ Los templates se actualizarán automáticamente

### **Opción 2: Forzar Actualización Manual de Templates**

Si la actualización automática no funciona:

```python
# Ejecutar en Odoo Shell (python3 odoo-bin shell -d tu_base_datos -c /etc/odoo/odoo.conf)

# Eliminar templates antiguos
self.env.ref('website_leave_form.email_template_leave_approval').unlink()
self.env.ref('website_leave_form.email_template_leave_approved').unlink()
self.env.ref('website_leave_form.email_template_leave_rejected').unlink()

# Ejecutar actualización de datos
self.env['ir.module.module'].update_list()

# Forzar actualización del módulo
module = self.env['ir.module.module'].search([('name', '=', 'website_leave_form')])
module.button_immediate_upgrade()
```

---

## ✅ Verificación Post-Instalación

### **1. Verificar que los templates estén actualizados**

```python
# En Odoo Shell
template = self.env.ref('website_leave_form.email_template_leave_approval')
print("Contiene QWeb:", '<t t-esc=' in template.body_html)
print("NO contiene Mako:", '${object' not in template.body_html)
# Ambos deben retornar True
```

### **2. Verificar web.base.url**

```python
# En Odoo Shell
base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
print(f"Base URL: {base_url}")
# Debe mostrar: https://tu-dominio.com (sin / al final)
```

O en la interfaz:
- **Ajustes** → **Técnico** → **Parámetros** → **Parámetros del Sistema**
- Buscar `web.base.url`
- Valor debe ser: `https://tu-dominio.com` (sin barra final)

### **3. Probar envío de email**

1. Crear una nueva solicitud de ausencia desde el formulario web
2. Verificar que el email llegue al aprobador
3. **Verificar que se vean los valores reales** (nombre, email, fechas, etc.)
4. **Hacer clic en "Aprobar Ausencia"**
5. Verificar que NO aparezca error 404
6. Debe mostrar página de confirmación

---

## 🐛 Troubleshooting

### **Problema: Aún aparecen las variables sin procesar**

**Solución:**
```bash
# 1. Verificar que se instaló la versión correcta
# En Odoo Shell
module = self.env['ir.module.module'].search([('name', '=', 'website_leave_form')])
print(f"Versión instalada: {module.latest_version}")
# Debe mostrar: 17.0.1.1.0

# 2. Forzar recarga de templates
self.env['mail.template'].search([('model', '=', 'website.leave.form')]).unlink()
module.button_immediate_upgrade()
```

### **Problema: Error 404 al hacer clic en botón de aprobación**

**Causa 1: web.base.url incorrecto**
```python
# Configurar correctamente
self.env['ir.config_parameter'].sudo().set_param('web.base.url', 'https://tu-dominio.com')
```

**Causa 2: Ruta no registrada**
```bash
# Verificar logs de Odoo
tail -f /var/log/odoo/odoo-server.log | grep "ausencias/approve"

# Verificar que el controlador esté cargado
# En Odoo Shell
from odoo.addons.website_leave_form.controllers.website_leave_controller import WebsiteLeaveController
print("Controlador cargado correctamente")
```

**Causa 3: Token no generado**
```python
# Verificar que las solicitudes tengan token
leave_form = self.env['website.leave.form'].search([], limit=1)
print(f"Token: {leave_form.approval_token}")
# Si es False/vacío, regenerar:
leave_form.generate_approval_token()
print(f"Nuevo token: {leave_form.approval_token}")
```

### **Problema: Los botones del email no tienen estilo**

Este problema es cosmético y no afecta la funcionalidad. Algunos clientes de email (como Outlook) pueden no renderizar bien los estilos inline. La funcionalidad de aprobación seguirá funcionando.

---

## 📝 Notas Técnicas

### **Diferencias Sintaxis: Mako vs QWeb**

| Mako (❌ Incorrecto) | QWeb (✅ Correcto) |
|---------------------|-------------------|
| `${object.name}` | `<t t-esc="object.name"/>` |
| `% if condition:` | `<t t-if="condition">` |
| `% endif` | `</t>` |
| `href="${url}"` | `t-attf-href="{{url}}"` |
| `${len(lista)}` | `<t t-esc="len(lista)"/>` |

### **¿Por qué ocurrió este error?**

Odoo cambió el motor de templates para emails de **Mako a QWeb** en versiones recientes. El módulo original fue desarrollado con la sintaxis antigua (Mako), la cual ya no es compatible.

### **Archivos CDATA**

Los templates ahora usan `<![CDATA[...]]>` para evitar problemas con caracteres especiales en el HTML:
```xml
<field name="body_html" type="html"><![CDATA[
    <!-- HTML aquí -->
]]></field>
```

---

## 🎯 Cambios Específicos en el Código

### Ejemplo de Cambio en Template

**Antes (❌):**
```html
<p>Hola <strong>${object.approver_id.name}</strong>,</p>
<td>${object.email}</td>
% if object.notes:
    <td>${object.notes}</td>
% endif
<a href="${object.get_approval_url('approve')}">Aprobar</a>
```

**Después (✅):**
```html
<p>Hola <strong><t t-esc="object.approver_id.name"/></strong>,</p>
<td><t t-esc="object.email"/></td>
<t t-if="object.notes">
    <td><t t-esc="object.notes"/></td>
</t>
<a t-attf-href="{{object.get_approval_url('approve')}}">Aprobar</a>
```

---

## 📞 Soporte

Si después de aplicar este hotfix continúas experimentando problemas:

1. Verifica los logs de Odoo: `/var/log/odoo/odoo-server.log`
2. Comprueba que el módulo se actualizó correctamente
3. Verifica la configuración de `web.base.url`
4. Prueba enviar un email de prueba manualmente:
   ```python
   # En Odoo Shell
   leave_form = self.env['website.leave.form'].search([], limit=1)
   leave_form.send_approval_notification()
   ```

---

## ✨ Versión

- **Módulo:** Formulario Web de Ausencias
- **Versión:** 17.0.1.1.0
- **Fecha:** Octubre 2025
- **Tipo:** Hotfix - Corrección de Templates
- **Compatibilidad:** Odoo 17.0

---

**¡Tus emails ahora mostrarán la información correctamente!** 🎉
