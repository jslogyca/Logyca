# Calculadora de Descuentos Condicionados en Ventas

## Descripción

Este módulo permite calcular descuentos condicionados en órdenes de venta de Odoo 17 según parámetros configurables de porcentajes de aumento y descuento con dos fechas diferentes.

## Características Principales

### 1. Wizard de Búsqueda y Cálculo
- **Filtrado por campo x_origen**: Permite buscar órdenes de venta específicas según un valor del campo personalizado `x_origen`
- **Rango de fechas**: Filtra las órdenes dentro de un período específico
- **Selección múltiple**: Permite seleccionar o deseleccionar todas las órdenes encontradas, o marcar individualmente
- **Dos períodos de descuento**: Calcula descuentos para dos fechas diferentes con parámetros independientes

### 2. Cálculo de Descuentos

El módulo calcula automáticamente dos tipos de descuentos condicionados:

#### Fórmula de Cálculo
Para cada línea de la orden de venta:
```
descuento_linea = ((((precio_unitario * cantidad) / (porcentaje_aumento + 1)) * porcentaje_aumento) * porcentaje_descuento)
```

#### Descuento Condicionado 1
- Parámetros: % Aumento 1, % Descuento 1, Fecha 1
- Campos actualizados en `sale.order`:
  - `x_conditional_discount`: Valor del descuento
  - `x_conditional_discount_deadline`: Fecha límite
  - `x_amount_total_conditional_discount`: Total con descuento (amount_total - descuento)

#### Descuento Condicionado 2
- Parámetros: % Aumento 2, % Descuento 2, Fecha 2
- Campos actualizados en `sale.order`:
  - `x_conditional_discount_second_date`: Valor del descuento
  - `x_conditional_discount_deadline_second_date`: Fecha límite
  - `x_amount_total_conditional_discount_second_date`: Total con descuento

### 3. Actualización Automática de Facturas

Si la orden de venta tiene una factura asociada (`account.move` con `move_type='out_invoice'` y `state='posted'`), el módulo actualiza automáticamente los siguientes campos:

**Para el primer descuento:**
- `x_value_discounts` ← `x_conditional_discount`
- `x_discounts_deadline` ← `x_conditional_discount_deadline`
- `x_amount_total_discounts` ← `x_amount_total_conditional_discount`

**Para el segundo descuento:**
- `x_value_discounts_second_date` ← `x_conditional_discount_second_date`
- `x_discounts_deadline_second_date` ← `x_conditional_discount_deadline_second_date`
- `x_amount_total_discounts_second_date` ← `x_amount_total_conditional_discount_second_date`

## Instalación

1. Copiar el módulo `sale_conditional_discount_calculator` en el directorio de addons de Odoo
2. Actualizar la lista de módulos en Odoo
3. Buscar el módulo "Calculadora de Descuentos Condicionados en Ventas"
4. Hacer clic en "Instalar"

## Uso

### Paso 1: Acceder al Wizard
Ir a: **Ventas > Calcular Descuentos Condicionados**

### Paso 2: Configurar Criterios de Búsqueda
- **Filtro x_origen**: Ingresar el valor del campo x_origen a buscar (ej: "ECOMMERCE")
- **Fecha Desde**: Fecha inicial del rango
- **Fecha Hasta**: Fecha final del rango

### Paso 3: Configurar Parámetros de Descuento

**Primer Descuento:**
- % Aumento Fecha 1 (ej: 19 para 19%)
- % Descuento Fecha 1 (ej: 3 para 3%)
- Fecha Descuento 1 (fecha límite de aplicación)

**Segundo Descuento:**
- % Aumento Fecha 2 (ej: 19 para 19%)
- % Descuento Fecha 2 (ej: 2 para 2%)
- Fecha Descuento 2 (fecha límite de aplicación)

### Paso 4: Buscar Órdenes
Hacer clic en **"Buscar Órdenes"**

El sistema mostrará todas las órdenes que cumplan con:
- Campo x_origen igual al valor especificado
- Fecha de orden dentro del rango
- Estado: Sale o Done
- Mostrará la factura asociada si existe

### Paso 5: Seleccionar Órdenes
- **Seleccionar Todas**: Marca todas las órdenes
- **Deseleccionar Todas**: Desmarca todas las órdenes
- También puede marcar/desmarcar individualmente cada línea

### Paso 6: Calcular Descuentos
Hacer clic en **"Calcular Descuentos"**

El sistema:
1. Aplicará la fórmula de cálculo a cada línea de las órdenes seleccionadas
2. Actualizará los campos de descuento en las órdenes
3. Actualizará los campos correspondientes en las facturas asociadas
4. Mostrará un mensaje de confirmación

## Visualización de Resultados

### En Órdenes de Venta
Los campos calculados aparecen en:
- Vista de formulario después del campo "Total"
- Pestaña "Descuentos Condicionados" con información detallada
- Vista de lista (campos opcionales)

### En Facturas
Los campos calculados aparecen en:
- Vista de formulario después del campo "Total" (solo para facturas de cliente)
- Pestaña "Descuentos Condicionados" con información detallada
- Vista de lista (campos opcionales)

## Estructura Técnica

```
sale_conditional_discount_calculator/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── sale_order.py
│   └── account_move.py
├── wizards/
│   ├── __init__.py
│   ├── sale_conditional_discount_wizard.py
│   └── sale_conditional_discount_wizard_views.xml
├── views/
│   ├── sale_order_views.xml
│   └── account_move_views.xml
├── security/
│   └── ir.model.access.csv
└── README.md
```

## Dependencias

- `sale`: Módulo de ventas de Odoo
- `account`: Módulo de contabilidad de Odoo

## Notas Importantes

1. **Campo x_origen**: El módulo asume que el modelo `sale.order` tiene un campo personalizado `x_origen`. Asegúrese de que este campo existe en su sistema.

2. **Facturas**: Solo se actualizan facturas en estado "Contabilizado" (`posted`) y tipo "Factura de Cliente" (`out_invoice`).

3. **Órdenes**: Solo se procesan órdenes en estado "Orden de Venta" (`sale`) o "Bloqueado" (`done`).

4. **Cálculos**: Los cálculos se realizan sobre todas las líneas de la orden (`order_line`) multiplicando precio unitario por cantidad.

5. **Permisos**: El módulo requiere permisos de usuario de ventas para su uso.

## Soporte

Para soporte o consultas sobre este módulo, contactar al equipo de desarrollo de LOGYCA.

## Licencia

LGPL-3

## Autor

LOGYCA - Asociación Colombiana de Automatización Comercial
