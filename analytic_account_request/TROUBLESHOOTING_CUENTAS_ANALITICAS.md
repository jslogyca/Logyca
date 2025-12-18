# Troubleshooting: Carga de Cuentas Analíticas en Formulario de Producto

## Problema
Las cuentas analíticas no se cargan cuando se selecciona una organización en el formulario web de solicitud de producto.

## Solución Implementada

### 1. Correcciones en el JavaScript (product_request_templates.xml)

**Cambios realizados:**
- Se cambió de `fetch()` a `XMLHttpRequest` para mejor compatibilidad
- Se mejoró el manejo de errores con logging en consola
- Se agregó conversión explícita a entero del company_id
- Se mejoró la validación de respuestas

**Código corregido:**
```javascript
var xhr = new XMLHttpRequest();
xhr.open('POST', '/producto/get_analytic_accounts', true);
xhr.setRequestHeader('Content-Type', 'application/json');

xhr.onload = function() {
    if (xhr.status === 200) {
        try {
            var data = JSON.parse(xhr.responseText);
            if (data.result && data.result.accounts && data.result.accounts.length > 0) {
                // Cargar cuentas...
            } else {
                // Mostrar mensaje de que no hay cuentas
            }
        } catch (e) {
            console.error('Error parsing JSON:', e);
        }
    }
};
```

### 2. Correcciones en el Controlador (analytic_account_request_controller.py)

**Mejoras implementadas:**
- Se agregó manejo de `**kwargs` para capturar parámetros adicionales
- Se mejoró la conversión de tipos (string a int)
- Se agregó logging detallado con traceback en caso de error
- Se agregó validación cuando no se proporciona company_id

## Cómo Verificar que Funciona

### 1. Verificar desde el Navegador

1. Abrir el formulario: `https://tu-dominio.com/producto/formulario`
2. Abrir la consola del navegador (F12 > Console)
3. Seleccionar una organización en el formulario
4. Observar la consola:
   - **Éxito**: No debe haber errores rojos
   - **Error**: Aparecerán mensajes de error específicos

### 2. Verificar en los Logs de Odoo

Los logs se guardan automáticamente en Odoo. Para verlos:

1. Ir a **Configuración > Técnico > Logging**
2. Buscar por:
   - `Get Analytic Accounts Success` - Si funcionó correctamente
   - `Get Analytic Accounts Error` - Si hubo un error
   - `Get Analytic Accounts - No Company ID` - Si no se envió el ID

### 3. Verificar que Existan Cuentas Analíticas

Antes de probar, asegúrate de que:

1. Tienes cuentas analíticas creadas
2. Las cuentas están asociadas a la compañía que seleccionas

Para verificar:
- Ir a **Contabilidad > Configuración > Contabilidad Analítica > Cuentas Analíticas**
- Verificar que cada cuenta tenga una compañía asignada

## Problemas Comunes y Soluciones

### Problema 1: El dropdown no cambia al seleccionar organización

**Causa**: JavaScript no se está ejecutando

**Solución**:
1. Limpiar caché del navegador (Ctrl+F5)
2. Verificar que no haya errores JavaScript en consola
3. Verificar que el módulo se haya actualizado correctamente

### Problema 2: Aparece "No hay cuentas analíticas"

**Causa**: No existen cuentas analíticas para esa compañía

**Solución**:
1. Ir a **Contabilidad > Configuración > Contabilidad Analítica > Cuentas Analíticas**
2. Crear al menos una cuenta analítica
3. Asignarla a la compañía correspondiente

### Problema 3: Error 404 en la consola

**Causa**: La ruta del endpoint no está registrada

**Solución**:
1. Reiniciar el servidor de Odoo
2. Actualizar el módulo
3. Verificar logs de Odoo al iniciar

### Problema 4: Error 500 en la consola

**Causa**: Error en el servidor al procesar la petición

**Solución**:
1. Revisar los logs de Odoo: `/var/log/odoo/odoo.log`
2. Buscar el traceback del error
3. Verificar que el modelo `account.analytic.account` exista
4. Verificar permisos del usuario

## Testing Manual

### Test 1: Carga Básica

```javascript
// Pegar en la consola del navegador cuando estés en el formulario
var companySelect = document.getElementById('company_id');
var analyticAccountSelect = document.getElementById('analytic_account_id');

console.log('Company Select:', companySelect);
console.log('Analytic Account Select:', analyticAccountSelect);

// Seleccionar la primera compañía
if (companySelect.options.length > 1) {
    companySelect.selectedIndex = 1;
    companySelect.dispatchEvent(new Event('change'));
}
```

**Resultado esperado**: 
- En unos segundos, el dropdown de cuentas analíticas debe mostrar las cuentas disponibles
- En la consola debe aparecer la estructura de la respuesta JSON

### Test 2: Verificar Endpoint Directamente

Puedes probar el endpoint directamente usando curl:

```bash
curl -X POST https://tu-dominio.com/producto/get_analytic_accounts \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "company_id": 1
    },
    "id": 1
  }'
```

**Resultado esperado**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "accounts": [
      {"id": 1, "name": "Cuenta Analítica 1"},
      {"id": 2, "name": "Cuenta Analítica 2"}
    ]
  }
}
```

## Debugging Avanzado

### Activar Modo Debug en JavaScript

Agregar al inicio del JavaScript del template:

```javascript
var DEBUG = true;

function log(message, data) {
    if (DEBUG) {
        console.log('[PRODUCTO DEBUG]', message, data || '');
    }
}

// Luego usar en el código:
log('Company ID seleccionado:', companyId);
log('Respuesta recibida:', data);
```

### Verificar Parámetros Recibidos en el Controlador

En el archivo `analytic_account_request_controller.py`, puedes agregar logging adicional:

```python
def get_analytic_accounts(self, company_id, **kwargs):
    # Agregar al inicio del método
    import logging
    _logger = logging.getLogger(__name__)
    _logger.info('=== GET ANALYTIC ACCOUNTS ===')
    _logger.info(f'company_id recibido: {company_id} (tipo: {type(company_id)})')
    _logger.info(f'kwargs: {kwargs}')
    
    # ... resto del código
```

## Contacto y Soporte

Si después de aplicar estas correcciones el problema persiste:

1. **Recopilar información**:
   - Captura de pantalla de la consola del navegador
   - Logs de Odoo del momento del error
   - Versión de Odoo que estás usando
   - Navegador y versión

2. **Verificar**:
   - ¿Se actualizó correctamente el módulo?
   - ¿Se reinició el servidor después de actualizar?
   - ¿Hay cuentas analíticas creadas?
   - ¿El usuario tiene permisos para ver cuentas analíticas?

3. **Contactar soporte** con toda la información recopilada

## Checklist de Verificación

- [ ] Módulo actualizado correctamente
- [ ] Servidor Odoo reiniciado
- [ ] Caché del navegador limpiado
- [ ] Existen cuentas analíticas en el sistema
- [ ] Las cuentas están asociadas a compañías
- [ ] No hay errores en consola del navegador
- [ ] No hay errores en logs de Odoo
- [ ] El endpoint responde correctamente
- [ ] El dropdown se actualiza al cambiar la organización
