# Script SQL de Migración para Actualización del Módulo

## Migración para Tarjetas de Crédito

Este script debe ejecutarse DESPUÉS de actualizar el módulo si ya existen registros de tarjetas de crédito en estado "approved".

```sql
-- Actualizar registros existentes en estado "approved" que no tengan fecha de aprobación
UPDATE credit_card_request
SET approval_date = write_date
WHERE state = 'approved' 
AND approval_date IS NULL;

-- Si hay registros que deben estar en "in_process" o "done", actualizar manualmente según sea necesario
-- Ejemplo: Mover solicitudes terminadas que estaban en "approved"
-- UPDATE credit_card_request SET state = 'done' WHERE id IN (...);
```

## Migración para Productos

Los nuevos campos de aprobación tienen valores por defecto (False para los booleanos), por lo que no es necesaria migración de datos. Sin embargo, si quieres marcar solicitudes existentes como aprobadas:

```sql
-- Marcar todas las aprobaciones como completas para solicitudes ya aprobadas
UPDATE product_request
SET financial_approved = true,
    legal_approved = true,
    accounting_approved = true,
    financial_approval_date = write_date,
    legal_approval_date = write_date,
    accounting_approval_date = write_date
WHERE state IN ('approved', 'done');
```

## Notas Importantes

1. **Hacer backup** de la base de datos antes de ejecutar cualquier script SQL
2. Estos scripts son opcionales y solo necesarios si tienes datos existentes
3. Para nuevas instalaciones, no es necesario ejecutar nada
4. Adaptar los scripts según las necesidades específicas de tu base de datos

## Verificación Post-Migración

```sql
-- Verificar tarjetas de crédito sin fecha de aprobación en estados aprobados
SELECT id, name, state, approval_date, approver_id
FROM credit_card_request
WHERE state IN ('approved', 'in_process', 'done')
ORDER BY create_date DESC;

-- Verificar productos con aprobaciones incompletas en estado aprobado
SELECT id, name, state, 
       financial_approved, legal_approved, accounting_approved
FROM product_request
WHERE state = 'approved'
ORDER BY create_date DESC;
```
