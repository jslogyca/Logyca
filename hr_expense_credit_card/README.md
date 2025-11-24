# HR Expense Credit Card - Legalización de Tarjetas de Crédito

## Versión 17.0.2.0.0

## Descripción

Módulo completo de personalización para Odoo 17.0 que permite la legalización integral de gastos realizados con tarjetas de crédito corporativas, incluyendo configuración centralizada de tarjetas y generación automática de asientos contables.

## Características Principales

### 1. Modelo de Configuración de Tarjetas de Crédito

Nuevo modelo `credit.card` para gestionar las tarjetas de crédito corporativas:

**Campos principales:**
- **Nombre**: Identificador de la tarjeta
- **Cuenta Contable**: Cuenta de CXP asociada a la tarjeta
- **Tercero/Proveedor**: Banco emisor de la tarjeta
- **Compañía**: Compañía a la que pertenece la tarjeta
- **Últimos 4 dígitos**: Para identificación
- **Tipo de Tarjeta**: Visa, Mastercard, Amex, Diners, Otra
- **Cupo**: Límite de crédito de la tarjeta

**Ubicación del menú**: Gastos > Configuración > Tarjetas de Crédito

### 2. Proveedor en Gastos Individuales (hr.expense)

- Campo `partner_id` para seleccionar el proveedor que generó el gasto
- Opción "Tarjeta de Crédito" en el campo "Pagado por" (payment_mode)
- Campos visibles en vistas: formulario, árbol y kanban

### 3. Selección de Tarjeta en Reportes de Gastos

En el reporte de gastos (hr.expense.sheet):
- Campo `credit_card_id` para seleccionar la tarjeta utilizada
- Campo **obligatorio** cuando payment_mode = 'credit_card'
- Auto-completado del proveedor de la tarjeta
- Campo `journal_id` visible cuando se selecciona tarjeta de crédito

### 4. Acceso a Asientos Contables

- Botón "Asientos" en el formulario del reporte
- Acceso directo a los asientos contables generados
- Contador de asientos generados

### 5. Generación Automática de Asientos Contables

Cuando se contabiliza un reporte con tarjeta de crédito:

#### Por cada gasto individual:
**Líneas de Débito:**
- Cuenta del gasto
- Proveedor del gasto
- Monto del gasto
- Líneas adicionales por impuestos (si aplica)

**Línea de Crédito (CXP):**
- Cuenta de la tarjeta de crédito (configurada en credit.card)
- Tercero de la tarjeta (configurado en credit.card)
- Monto total del gasto

## Instalación

1. Copiar el módulo en la carpeta de addons de Odoo
2. Actualizar la lista de aplicaciones
3. Buscar "HR Expense Credit Card" e instalar

## Dependencias

- `hr_expense` (Módulo base de gastos de Odoo)
- `account` (Módulo de contabilidad de Odoo)

## Configuración Inicial

### 1. Configurar Tarjetas de Crédito

**Ruta**: Gastos > Configuración > Tarjetas de Crédito

1. Hacer clic en "Crear"
2. Completar los campos obligatorios:
   - **Nombre**: Ej. "Tarjeta Corporativa Principal"
   - **Cuenta Contable**: Seleccionar cuenta de CXP (Ej: 220505)
   - **Tercero/Proveedor**: Seleccionar el banco emisor
3. Opcionalmente completar:
   - Últimos 4 dígitos
   - Tipo de tarjeta
   - Cupo
4. Guardar

### 2. Configurar Categorías de Gastos

**Ruta**: Gastos > Configuración > Categorías de Gastos

Verificar que cada categoría tenga:
- ✅ "Puede ser gastado" activado
- ✅ Cuenta de Gastos configurada

### 3. Registrar Proveedores

**Ruta**: Contactos

Registrar los proveedores donde se realizan gastos:
- Restaurantes
- Taxis
- Hoteles
- Etc.

## Flujo de Uso Completo

### Paso 1: Crear Gastos Individuales

**Ruta**: Gastos > Mis Gastos > Crear

1. Seleccionar categoría (Ej: Almuerzos)
2. En "Pagado por", seleccionar: **Tarjeta de Crédito**
3. **Seleccionar el proveedor** del gasto (Ej: Restaurante)
4. Ingresar monto y otros datos
5. Agregar impuestos si aplica
6. Guardar

### Paso 2: Crear Reporte de Gastos

**Ruta**: Gastos > Mis Reportes > Crear

1. Dar un nombre al reporte
2. Agregar los gastos (todos deben ser con payment_mode = 'credit_card')
3. El sistema mostrará automáticamente:
   - Campo "Diario" (journal_id) - visible
   - Campo "Tarjeta de Crédito" - **obligatorio**
4. **Seleccionar la tarjeta de crédito** utilizada
5. Seleccionar el diario contable
6. Enviar para aprobación

### Paso 3: Aprobar y Contabilizar

1. El manager aprueba el reporte
2. Hacer clic en "Contabilizar"
3. El sistema genera automáticamente el asiento contable

### Paso 4: Ver Asiento Contable

1. Desde el reporte, hacer clic en el botón "Asientos" (parte superior)
2. Se abrirá el asiento contable generado
3. Verificar las líneas:
   - Débitos por cada gasto con su proveedor
   - Créditos (CXP) con la cuenta y tercero de la tarjeta

## Ejemplo de Asiento Contable Generado

### Escenario:
- **Tarjeta**: Tarjeta Corporativa Principal
- **Cuenta de la tarjeta**: 220505 - CXP Banco Nacional
- **Tercero de la tarjeta**: Banco Nacional S.A.

### Gastos:
1. Almuerzo - Restaurante Central - $50.000
2. Taxi - Taxi Express - $30.000 + IVA 19% ($5.700)

### Asiento Generado:

```
Diario: Compras
Fecha: 2024-11-24
Referencia: GASTOS/2024/001

┌────────────────────────────────────────────────────────────────────┐
│ Cuenta              │ Proveedor          │ Débito │ Crédito │ Desc │
├────────────────────────────────────────────────────────────────────┤
│ 510506 Almuerzos    │ Rest. Central      │ 50.000 │    0.00 │ Alm  │
│ 220505 CXP Banco    │ Banco Nacional     │   0.00 │ 50.000  │ CXP  │
│ 510515 Transporte   │ Taxi Express       │ 30.000 │    0.00 │ Taxi │
│ 240801 IVA          │ Taxi Express       │  5.700 │    0.00 │ IVA  │
│ 220505 CXP Banco    │ Banco Nacional     │   0.00 │ 35.700  │ CXP  │
├────────────────────────────────────────────────────────────────────┤
│ TOTAL                                    │ 85.700 │ 85.700  │      │
└────────────────────────────────────────────────────────────────────┘
```

**Observaciones importantes:**
- Cada gasto genera una línea de débito con su proveedor
- Cada gasto genera una línea de crédito CXP con la cuenta y tercero de la tarjeta
- Los impuestos se contabilizan con el proveedor del gasto
- El asiento queda cuadrado y publicado automáticamente

## Validaciones Implementadas

El módulo incluye las siguientes validaciones:

- ✅ La tarjeta de crédito es obligatoria cuando payment_mode = 'credit_card'
- ✅ Todos los gastos deben tener un proveedor asignado
- ✅ Todos los gastos deben tener una cuenta contable configurada
- ✅ La tarjeta debe tener configurada una cuenta contable
- ✅ La tarjeta debe tener configurado un tercero/proveedor
- ✅ Los últimos 4 dígitos deben ser numéricos (si se ingresan)
- ✅ El nombre de la tarjeta debe ser único por compañía

## Estructura Técnica

```
hr_expense_credit_card/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── credit_card.py           # ⭐ NUEVO: Modelo de tarjetas
│   ├── hr_expense.py            # Extensión con payment_mode
│   └── hr_expense_sheet.py      # Lógica de contabilización
├── views/
│   ├── credit_card_views.xml    # ⭐ NUEVO: Vistas de tarjetas
│   ├── hr_expense_views.xml
│   └── hr_expense_sheet_views.xml
├── security/
│   └── ir.model.access.csv      # Permisos actualizados
├── data/
│   └── credit_card_demo.xml     # ⭐ NUEVO: Datos demo
└── README.md
```

## Modelos y Campos

### Modelo: credit.card (NUEVO)
- `name` (Char): Nombre de la tarjeta
- `account_id` (Many2one): Cuenta contable de CXP
- `partner_id` (Many2one): Tercero/Proveedor (banco)
- `company_id` (Many2one): Compañía
- `active` (Boolean): Estado activo/archivado
- `card_number` (Char): Últimos 4 dígitos
- `card_type` (Selection): Tipo de tarjeta
- `credit_limit` (Monetary): Cupo de la tarjeta
- `currency_id` (Many2one): Moneda
- `notes` (Text): Observaciones

### Modelo: hr.expense
- `partner_id` (Many2one): Proveedor del gasto
- `payment_mode` (Selection): Agregada opción 'credit_card'

### Modelo: hr.expense.sheet
- `credit_card_id` (Many2one): Tarjeta utilizada ⭐ NUEVO
- `credit_card_partner_id` (Many2one): Proveedor de la tarjeta (auto-completado)

## Métodos Principales

### credit.card
- `name_get()`: Personaliza la visualización del nombre (incluye últimos 4 dígitos)
- `_check_card_number()`: Valida que los últimos 4 dígitos sean numéricos

### hr.expense.sheet
- `_onchange_credit_card_id()`: Auto-completa el proveedor al seleccionar tarjeta ⭐ NUEVO
- `_prepare_expense_credit_card_move_vals()`: Genera las líneas del asiento (actualizado)
- `action_sheet_move_create()`: Crea y publica el asiento contable
- `action_view_account_moves()`: Abre los asientos generados ⭐ NUEVO

## Permisos de Seguridad

### credit.card
- **Usuarios de Gastos**: Solo lectura
- **Aprobadores de Gastos**: Lectura, escritura y creación
- **Managers de Contabilidad**: Control total

## Mejoras Implementadas

### Versión 17.0.2.0.0 (ACTUAL)

1. ✅ Modelo de configuración de tarjetas de crédito
2. ✅ Campo de tarjeta en reportes de gastos (obligatorio)
3. ✅ Generación de CXP por cada gasto individual
4. ✅ Cuenta y tercero de la tarjeta configurables
5. ✅ Botón para acceder a asientos desde el reporte
6. ✅ Campo journal_id visible con tarjeta de crédito
7. ✅ Auto-completado del proveedor de la tarjeta
8. ✅ Datos demo para pruebas rápidas

### Versión 17.0.1.0.0 (ANTERIOR)
- Campo de proveedor en gastos
- Opción "Tarjeta de Crédito" en payment_mode
- Contabilización básica

## Casos de Uso

### Caso 1: Gasto Simple sin Impuestos
```
Gasto: $100.000
Proveedor gasto: Proveedor A
Tarjeta: Tarjeta 1 (Cuenta: 220505, Tercero: Banco X)

Asiento:
Débito:  510506 - Proveedor A - $100.000
Crédito: 220505 - Banco X     - $100.000
```

### Caso 2: Gasto con IVA
```
Gasto: $100.000 + IVA 19% ($19.000)
Proveedor gasto: Proveedor B
Tarjeta: Tarjeta 1 (Cuenta: 220505, Tercero: Banco X)

Asiento:
Débito:  510515 - Proveedor B - $100.000
Débito:  240801 - Proveedor B - $ 19.000
Crédito: 220505 - Banco X     - $119.000
```

### Caso 3: Múltiples Gastos
```
Gasto 1: $50.000 - Proveedor A
Gasto 2: $75.000 - Proveedor B
Tarjeta: Tarjeta 1 (Cuenta: 220505, Tercero: Banco X)

Asiento:
Débito:  510506 - Proveedor A - $50.000
Crédito: 220505 - Banco X     - $50.000
Débito:  510515 - Proveedor B - $75.000
Crédito: 220505 - Banco X     - $75.000
Total: $125.000 débitos / $125.000 créditos
```

## Troubleshooting

### Problema: No aparece el campo "Tarjeta de Crédito"
**Solución**: Verificar que todos los gastos del reporte tengan payment_mode = 'credit_card'

### Problema: Error al contabilizar "Debe seleccionar la tarjeta de crédito"
**Solución**: Seleccionar una tarjeta de crédito en el campo obligatorio del reporte

### Problema: No puedo crear tarjetas de crédito
**Solución**: Verificar permisos de usuario (mínimo: Aprobador de Gastos)

### Problema: La cuenta o tercero no aparecen
**Solución**: Verificar que la tarjeta de crédito tenga configurados ambos campos

## Soporte

Para soporte o consultas:
- Empresa: LOGYCA
- Website: https://www.logyca.com

## Changelog

### 17.0.2.0.0 (2024-11-24)
- Agregado modelo credit.card para configuración de tarjetas
- Generación de CXP por cada gasto individual
- Botón de acceso a asientos contables
- Campo journal_id visible con tarjeta de crédito
- Datos demo para pruebas

### 17.0.1.0.0 (2024-11-20)
- Versión inicial
- Campo de proveedor en gastos
- Opción "Tarjeta de Crédito"
- Contabilización básica

## Licencia

LGPL-3
