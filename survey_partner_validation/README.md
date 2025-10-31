# Survey Partner Validation

## Descripción
Este módulo para Odoo permite vincular respuestas de encuestas con terceros (res.partner) basándose en el NIT y valida que los terceros creados después del 31 de octubre de 2025 tengan una encuesta completada antes de poder publicar facturas.

## Características

### 1. Asociación de Tercero por NIT
- Añade un botón "Asociar Tercero por NIT" en las respuestas de encuesta (`survey.user_input`)
- Busca automáticamente el tercero cuyo VAT coincida con el nickname (donde se guarda el NIT)
- Asocia la encuesta al tercero encontrado
- Muestra notificación de éxito o error

### 2. Validación de Encuestas en Facturas
- Los terceros creados después del 31/10/2025 requieren completar una encuesta
- Al intentar publicar una factura, el sistema valida:
  - Si el tercero fue creado después del 31/10/2025
  - Si tiene al menos una encuesta en estado "done" (completada)
- Bloquea la publicación de la factura si no cumple los requisitos
- Muestra mensaje de error explicativo

### 3. Información en Terceros (res.partner)
- **Campo "Requiere Encuesta"**: Indica si fue creado después del 31/10/2025
- **Campo "Encuesta Completada"**: Indica si tiene encuestas completadas
- **Botón inteligente**: Muestra el número de encuestas asociadas
- **Pestaña "Encuestas"**: 
  - Muestra alertas visuales según el estado
  - Lista todas las encuestas asociadas al tercero

## Instalación

1. Copiar el módulo a la carpeta de addons de Odoo
2. Actualizar la lista de aplicaciones
3. Buscar "Survey Partner Validation"
4. Instalar el módulo

## Uso

### Asociar una encuesta a un tercero:

1. Ir a **Encuestas > Respuestas**
2. Abrir una respuesta que tenga el NIT en el campo "Apodo" (nickname)
3. Hacer clic en el botón **"Asociar Tercero por NIT"**
4. El sistema buscará el tercero con ese VAT y lo asociará automáticamente

### Verificar el estado de encuestas de un tercero:

1. Ir a **Contactos**
2. Abrir un tercero
3. Ir a la pestaña **"Encuestas"**
4. Verificar:
   - Si requiere encuesta
   - Si tiene encuesta completada
   - Ver alertas de estado

### Publicar una factura:

1. Crear una factura de cliente
2. Al hacer clic en **"Publicar"**:
   - Si el tercero fue creado después del 31/10/2025 y NO tiene encuesta completada → **Error**
   - Si el tercero fue creado antes del 31/10/2025 → **Permite publicar**
   - Si el tercero tiene encuesta completada → **Permite publicar**

## Estructura del Módulo

```
survey_partner_validation/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── survey_user_input.py    # Extensión de respuestas de encuesta
│   ├── res_partner.py           # Extensión de terceros
│   └── account_move.py          # Extensión de facturas
├── views/
│   ├── survey_user_input_views.xml
│   └── res_partner_views.xml
├── security/
│   └── ir.model.access.csv
└── README.md
```

## Dependencias

- `base`: Módulo base de Odoo
- `survey`: Módulo de encuestas
- `account`: Módulo de contabilidad

## Notas Técnicas

### Fecha de corte
La fecha de corte es el **31 de octubre de 2025 a las 23:59:59**. Los terceros creados después de esta fecha requieren encuesta.

### Estado de encuesta
Una encuesta se considera completada cuando su campo `state` es igual a `'done'`.

### Tipos de factura validados
Solo se validan facturas de cliente:
- `out_invoice`: Factura de cliente
- `out_refund`: Nota de crédito de cliente

## Soporte

Para soporte o consultas, contactar al administrador del sistema.

## Versión
1.0 - Versión inicial

## Licencia
Propietario
