# Guía de Actualización - HR Expense Credit Card

## Actualización de versión 17.0.1.0.0 a 17.0.2.0.0

### Cambios Principales

1. **Nuevo Modelo**: `credit.card` para configuración de tarjetas
2. **Nuevo Campo**: `credit_card_id` en `hr.expense.sheet` (reemplaza a `credit_card_partner_id`)
3. **Nueva Lógica**: Generación de CXP por cada gasto individual
4. **Nueva Funcionalidad**: Botón de acceso a asientos contables
5. **Mejora**: Campo `journal_id` visible cuando se usa tarjeta de crédito

### Pasos de Actualización

#### 1. Backup de la Base de Datos
```bash
# IMPORTANTE: Hacer backup antes de actualizar
pg_dump -U odoo -d tu_database > backup_$(date +%Y%m%d).sql
```

#### 2. Desinstalar Versión Anterior (Opcional)
Si quieres hacer una instalación limpia:
```bash
# Desde Odoo
Aplicaciones > HR Expense Credit Card > Desinstalar
```

#### 3. Reemplazar Archivos del Módulo
```bash
cd /path/to/odoo/addons
rm -rf hr_expense_credit_card
unzip hr_expense_credit_card.zip
```

#### 4. Actualizar el Módulo
```bash
# Opción 1: Línea de comandos
./odoo-bin -d tu_database -u hr_expense_credit_card --stop-after-init

# Opción 2: Desde la interfaz
Aplicaciones > Actualizar Lista de Aplicaciones
Buscar "HR Expense Credit Card" > Actualizar
```

#### 5. Configurar Tarjetas de Crédito

**IMPORTANTE**: Después de actualizar, debes configurar las tarjetas de crédito.

**Ruta**: Gastos > Configuración > Tarjetas de Crédito

Para cada tarjeta que usabas antes:
1. Crear nueva tarjeta
2. Completar:
   - Nombre
   - Cuenta Contable (la que antes usabas en el diario)
   - Tercero/Proveedor (el que antes seleccionabas en credit_card_partner_id)
3. Guardar

#### 6. Migración de Datos (Si es necesario)

Si tienes reportes de gastos pendientes con la versión anterior:

**Opción A: Manual**
1. Ir a cada reporte pendiente
2. Seleccionar la tarjeta de crédito correspondiente
3. Guardar

**Opción B: Script SQL** (Avanzado)
```sql
-- Este script es solo un ejemplo, ajustar según tu configuración
-- HACER BACKUP ANTES DE EJECUTAR

-- Si tienes un solo banco y una sola tarjeta
UPDATE hr_expense_sheet
SET credit_card_id = (SELECT id FROM credit_card LIMIT 1)
WHERE credit_card_partner_id IS NOT NULL
AND credit_card_id IS NULL;
```

### Verificación Post-Actualización

#### 1. Verificar Modelo de Tarjetas
- [ ] Ir a: Gastos > Configuración > Tarjetas de Crédito
- [ ] Verificar que aparece el menú
- [ ] Crear una tarjeta de prueba
- [ ] Verificar que se guarda correctamente

#### 2. Verificar Reportes de Gastos
- [ ] Crear un gasto con payment_mode = 'credit_card'
- [ ] Crear un reporte con ese gasto
- [ ] Verificar que aparece el campo "Tarjeta de Crédito"
- [ ] Verificar que el campo "Diario" está visible
- [ ] Seleccionar una tarjeta
- [ ] Verificar que se auto-completa el proveedor

#### 3. Verificar Contabilización
- [ ] Aprobar el reporte de prueba
- [ ] Contabilizar
- [ ] Hacer clic en el botón "Asientos" (arriba)
- [ ] Verificar que el asiento tiene:
  - Líneas de débito por cada gasto
  - Líneas de crédito CXP con cuenta y tercero de la tarjeta
  - Total cuadrado

### Cambios en el Flujo de Trabajo

#### Antes (v17.0.1.0.0):
1. Crear gastos con proveedor
2. En reporte, seleccionar proveedor de tarjeta manualmente
3. Contabilizar → Una sola línea CXP total

#### Ahora (v17.0.2.0.0):
1. **Configurar tarjetas de crédito** (una vez)
2. Crear gastos con proveedor
3. En reporte, **seleccionar tarjeta de crédito** (obligatorio)
4. Contabilizar → **Una línea CXP por cada gasto**

### Ventajas de la Nueva Versión

1. ✅ **Configuración centralizada** de tarjetas
2. ✅ **Trazabilidad mejorada** - CXP por cada gasto
3. ✅ **Acceso directo** a asientos contables
4. ✅ **Auto-completado** del proveedor
5. ✅ **Validaciones mejoradas**
6. ✅ **Datos demo** para pruebas

### Problemas Conocidos y Soluciones

#### Problema 1: "Campo credit_card_id no existe"
**Causa**: La actualización no se completó correctamente
**Solución**:
```bash
./odoo-bin -d tu_database -u hr_expense_credit_card --stop-after-init
```

#### Problema 2: Reportes antiguos no tienen tarjeta seleccionada
**Causa**: Normal, son reportes creados con la versión anterior
**Solución**: 
- Para reportes pendientes: Editar y seleccionar tarjeta
- Para reportes ya contabilizados: No requiere acción

#### Problema 3: No aparece el menú de Tarjetas de Crédito
**Causa**: Permisos de usuario
**Solución**: Verificar que el usuario tiene grupo "Aprobador de Gastos" o superior

### Rollback (Si es necesario)

Si encuentras problemas y necesitas volver a la versión anterior:

```bash
# 1. Restaurar backup
psql -U odoo -d tu_database < backup_YYYYMMDD.sql

# 2. Instalar versión anterior del módulo
cd /path/to/odoo/addons
rm -rf hr_expense_credit_card
unzip hr_expense_credit_card_v1.zip

# 3. Reiniciar Odoo
sudo systemctl restart odoo
```

### Soporte

Si tienes problemas con la actualización:
1. Revisar logs de Odoo: `/var/log/odoo/odoo.log`
2. Verificar que hiciste backup
3. Contactar soporte: LOGYCA - https://www.logyca.com

### Testing Post-Actualización

Ejecutar estos tests para verificar que todo funciona:

**Test 1: Configuración de Tarjeta**
```
1. Crear tarjeta de crédito
2. Verificar que se guarda
3. Verificar que aparece en el selector
✓ PASS / ✗ FAIL
```

**Test 2: Flujo Completo**
```
1. Crear gasto con tarjeta de crédito
2. Crear reporte y seleccionar tarjeta
3. Aprobar
4. Contabilizar
5. Verificar asiento (botón "Asientos")
✓ PASS / ✗ FAIL
```

**Test 3: Asiento Contable**
```
1. Verificar líneas de débito por cada gasto
2. Verificar líneas de crédito con cuenta de tarjeta
3. Verificar tercero de la tarjeta en CXP
4. Verificar que asiento cuadra
✓ PASS / ✗ FAIL
```

---

**Actualización exitosa!** ✅

Si todos los tests pasan, la actualización se completó correctamente.
