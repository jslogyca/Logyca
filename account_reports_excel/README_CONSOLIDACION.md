# Consolidación por Cuenta Contable

## Descripción

Este módulo agrega funcionalidad para consolidar valores por cuenta contable en Odoo, mostrando:

1. **Total en Moneda Extranjera**: Suma de todos los valores `amount_currency` de los apuntes contables (`account.move.line`) donde la moneda es diferente a la moneda local de la compañía.

2. **Balance Total**: Suma de todos los valores `balance` de los apuntes contables de cada cuenta.

## Características Principales

### 1. Modelo de Reporte: `account.consolidation.report`

Este modelo utiliza una vista SQL materializada que consolida automáticamente los datos por cuenta contable.

**Campos principales:**
- `account_code`: Código de la cuenta contable
- `account_name`: Nombre de la cuenta contable
- `total_amount_currency`: Suma de valores en moneda extranjera
- `total_balance`: Suma total del balance
- `date_to`: Fecha de corte para el cálculo
- `count_lines`: Cantidad de apuntes contables
- `foreign_currency_id`: Moneda extranjera predominante

### 2. Wizard: `account.consolidation.wizard`

Permite seleccionar parámetros para generar el reporte:

**Opciones disponibles:**
- **Fecha de Corte**: Seleccione la fecha hasta la cual consolidar (por defecto: hoy)
- **Compañía**: Filtre por compañía específica
- **Cuentas Contables**: Seleccione cuentas específicas o deje vacío para todas
- **Solo moneda extranjera**: Marque para ver solo cuentas con valores en divisa extranjera

### 3. Vistas Disponibles

#### Vista Lista (Tree)
- Muestra todas las cuentas con sus consolidaciones
- Resalta las cuentas con moneda extranjera
- Incluye totales en el pie de página

#### Vista Pivot
- Análisis multidimensional de los datos
- Agrupación flexible por diferentes campos

#### Vista Gráfica
- Visualización de balances por cuenta
- Comparación entre moneda local y extranjera

## Uso

### Acceso al Reporte

1. **Desde el menú principal:**
   - Contabilidad → Informes → Consolidación por Cuenta

2. **Usando el Wizard:**
   - Contabilidad → Informes → Generar Consolidación
   - Seleccione la fecha de corte deseada
   - Configure los filtros opcionales
   - Haga clic en "Generar Reporte"

### Filtros Predefinidos

- **Con Moneda Extranjera**: Muestra solo cuentas con valores en divisa
- **Hoy**: Filtra por la fecha actual
- **Este Mes**: Filtra por el mes actual

### Agrupaciones

- Por Cuenta Contable
- Por Moneda Extranjera
- Por Compañía (en entornos multiempresa)

## Detalles Técnicos

### Consulta SQL

El modelo utiliza una vista SQL que:
1. Une las tablas `account_move_line`, `account_account` y `res_company`
2. Filtra solo apuntes en estado `posted` (contabilizados)
3. Agrupa por cuenta contable
4. Calcula sumas condicionales:
   - `total_amount_currency`: Solo cuando `currency_id` es diferente a la moneda de la compañía
   - `total_balance`: Suma de todos los balances

### Recálculo por Fecha

El método `get_consolidation_by_date(date_to)` permite obtener la consolidación para cualquier fecha específica, ejecutando una consulta SQL dinámica con el parámetro de fecha.

## Instalación

1. Copie el módulo en la carpeta de addons de Odoo
2. Actualice la lista de aplicaciones
3. Instale o actualice el módulo `account_reports_excel`
4. Los nuevos menús aparecerán en Contabilidad → Informes

## Requisitos

- Odoo 15.0 o superior
- Módulo `account` (Contabilidad)
- Módulo `logyca` (dependencia del módulo base)

## Permisos

El acceso al reporte está controlado por el grupo:
- `account_reports_excel.group_report_invoice_manager`

Los usuarios deben tener este permiso para ver y generar reportes.

## Archivos Nuevos Creados

```
account_reports_excel/
├── report/
│   ├── account_consolidation_report.py          # Modelo del reporte
│   └── account_consolidation_report_view.xml    # Vistas XML
├── wizard/
│   ├── account_consolidation_wizard.py          # Wizard Python
│   └── account_consolidation_wizard_view.xml    # Vista del wizard
└── security/
    └── ir.model.access.csv                      # Permisos (actualizado)
```

## Ejemplo de Uso

### Caso 1: Ver consolidación a la fecha actual
1. Navegue a: Contabilidad → Informes → Consolidación por Cuenta
2. El reporte se mostrará automáticamente con datos hasta hoy

### Caso 2: Ver consolidación a fecha específica
1. Navegue a: Contabilidad → Informes → Generar Consolidación
2. Seleccione la fecha de corte (ej: 31/12/2024)
3. Opcionalmente, marque "Solo cuentas con moneda extranjera"
4. Haga clic en "Generar Reporte"

### Caso 3: Exportar a Excel
1. Genere el reporte usando el wizard
2. Haga clic en "Exportar a Excel"
3. El archivo se descargará automáticamente

## Notas Importantes

- El reporte solo considera apuntes contables en estado `posted` (contabilizados)
- Los valores en moneda extranjera se muestran en la moneda original, no convertidos
- La fecha de corte filtra apuntes con `date <= fecha_seleccionada`
- El cálculo se realiza en tiempo real, por lo que siempre refleja los datos actuales

## Soporte

Para soporte o consultas, contacte al equipo de desarrollo de LOGYCA.
