# Guía de Instalación y Pruebas
## Módulo: Descuentos Comerciales Condicionados - Notas Crédito Automáticas

---

## 📋 REQUISITOS PREVIOS

### Sistema
- Odoo 17 instalado y funcionando
- Acceso de administrador al sistema
- Módulo de Contabilidad (`account`) instalado

### Configuración de Contabilidad
1. **Cuenta 530535 debe existir:**
   - Código: `530535`
   - Nombre: Descuentos Comerciales Condicionados
   - Tipo: Gastos

2. **Diario para Comprobantes de Reversión:**
   - Crear un diario de tipo "Miscellaneous" (General)
   - Nombre sugerido: "Reversión Descuentos Condicionados"
   - Código sugerido: "REVDC"

---

## 🔧 INSTALACIÓN

### Opción 1: Instalación Manual

1. **Copiar el módulo:**
   ```bash
   cp -r account_conditional_discount_report /ruta/a/odoo/addons/
   ```

2. **Establecer permisos:**
   ```bash
   sudo chown -R odoo:odoo /ruta/a/odoo/addons/account_conditional_discount_report
   sudo chmod -R 755 /ruta/a/odoo/addons/account_conditional_discount_report
   ```

3. **Reiniciar Odoo:**
   ```bash
   sudo systemctl restart odoo
   ```

4. **Actualizar lista de aplicaciones:**
   - Ir a: Aplicaciones
   - Hacer clic en "Actualizar lista de aplicaciones"
   - Buscar: "Reporte de Descuentos Comerciales Condicionados"
   - Hacer clic en "Instalar"

### Opción 2: Instalación por Línea de Comandos

```bash
# Copiar módulo
cp -r account_conditional_discount_report /ruta/a/odoo/addons/

# Instalar módulo
odoo-bin -c /etc/odoo/odoo.conf -d nombre_bd -i account_conditional_discount_report --stop-after-init

# Reiniciar servicio
sudo systemctl restart odoo
```

---

## ✅ VERIFICACIÓN DE INSTALACIÓN

### 1. Verificar Menú
- Ir a: **Contabilidad → Informes → Reportes**
- Debe aparecer: **"Descuentos Condicionados para NC"**

### 2. Verificar Modelo de Notas Crédito
- Ir a: **Configuración → Técnico → Estructura de Base de Datos → Modelos**
- Buscar: `account.move`
- Verificar que exista el campo: `is_conditional_discount_credit_note`

### 3. Verificar Permisos
- Usuario debe tener permisos de:
  - `Contabilidad / Facturación: Contable` o superior

---

## 🧪 PRUEBAS FUNCIONALES

### Escenario de Prueba 1: Crear Datos de Prueba

#### Paso 1: Crear Factura de Venta
```
Cliente: Cliente de Prueba
Productos: Cualquier producto
Subtotal: 1,000,000 COP
Total: 1,190,000 COP (con IVA 19%)
Estado: Publicada
```

#### Paso 2: Registrar Pago con Descuento
```
Diario: Banco (tipo: bank)
Monto Total Pago: 1,180,000 COP
Distribución:
  - 1,140,000 COP → CXC Cliente (pago neto)
  - 40,000 COP → Cuenta 530535 (descuento condicionado)
```

#### Paso 3: Conciliar Pago con Factura
```
Ir a la factura
Clic en "Registrar Pago"
Verificar que el pago esté conciliado
```

### Escenario de Prueba 2: Ejecutar el Proceso

#### Paso 1: Abrir Wizard
```
Ir a: Contabilidad → Informes → Reportes → Descuentos Condicionados para NC
```

#### Paso 2: Configurar Parámetros
```
Año: [Año actual]
Diario para Comprobantes de Reversión: [Seleccionar diario creado]
Cuenta de Descuentos (530535): [Seleccionar cuenta]
```

#### Paso 3: Cargar Facturas
```
Clic en: "Cargar Facturas"
```

**Resultado Esperado:**
- Se debe mostrar la factura creada en Paso 1
- Campo "Seleccionar" debe estar marcado
- Valor del descuento debe ser: 40,000 COP

#### Paso 4: Probar Selección
```
A. Clic en "Deseleccionar Todas"
   → Todas las facturas deben desmarcarse

B. Clic en "Seleccionar Todas"
   → Todas las facturas deben marcarse nuevamente

C. Deseleccionar manualmente una factura
   → Solo esa factura debe desmarcarse
```

#### Paso 5: Procesar
```
Clic en: "Procesar Notas Crédito"
Confirmar en el diálogo
```

**Resultado Esperado:**
- Mensaje de éxito
- Estado de la línea: "Procesado"
- Se deben haber creado:
  1. Una nota crédito
  2. Un comprobante de reversión

#### Paso 6: Verificar Documentos Creados

**Nota Crédito:**
```
Ir a: Contabilidad → Clientes → Notas Crédito
Buscar la nota crédito más reciente

Verificar:
- Tipo: Nota Crédito
- Cliente: Cliente de Prueba
- Monto: 40,000 COP
- Campo "NC por Descuento Condicionado": Sí (marcado)
- Estado: Publicada
- Referencia: [Número de factura original]
```

**Comprobante de Reversión:**
```
Ir a: Contabilidad → Contabilidad → Asientos Contables
Buscar el comprobante más reciente del diario de reversión

Verificar:
- Diario: [Diario de reversión configurado]
- Referencia: [Número de factura original]
- Estado: Publicada

Líneas:
1. Débito 40,000 → CXC Cliente
   - Descripción: "Reversion Descuento Condicionado - [Factura]"
2. Crédito 40,000 → Cuenta 530535
   - Descripción: "Reversion Descuento Condicionado - [Factura]"
```

#### Paso 7: Verificar Conciliación
```
Abrir la Nota Crédito
Ir a la pestaña "Apuntes Contables"
Verificar la línea de CXC:
- Debe mostrar "Conciliado" o el símbolo de conciliación
- Debe referenciar el comprobante de reversión
```

#### Paso 8: Descargar Reporte
```
Clic en: "Descargar Excel"

Verificar archivo Excel:
- Columna "Factura de Venta": [Número de factura]
- Columna "Valor Descuento": 40,000
- Columna "Nota Crédito": [Número de NC generada]
- Columna "Valor NC": 40,000
- Columna "Comprobante Reversión": [Número de comprobante]
- Columna "Valor Reversión": 40,000
- Columna "Estado": "Procesado"
- Columna "Error": (vacía)
```

### Escenario de Prueba 3: Prevención de Duplicados

#### Paso 1: Intentar Procesar la Misma Factura
```
1. Volver a abrir el wizard
2. Configurar mismo año
3. Clic en "Cargar Facturas"
```

**Resultado Esperado:**
- La factura ya procesada NO debe aparecer en la lista
- Debe incrementar el contador de "Registros Excluidos"

### Escenario de Prueba 4: Manejo de Errores

#### Simular Error (opcional)
```
1. Crear una factura sin cuenta de ingresos válida
2. Crear pago con descuento 530535
3. Conciliar
4. Ejecutar el proceso
```

**Resultado Esperado:**
- El estado de esa línea debe ser: "Error"
- Campo "Error" debe mostrar el mensaje descriptivo
- Las demás facturas válidas deben procesarse correctamente
- El reporte Excel debe incluir la información del error

---

## 🔍 VERIFICACIÓN DE INTEGRIDAD CONTABLE

### Balance de Cuentas

Después de procesar, verificar:

```
Cuenta CXC Cliente:
- Débito inicial: 1,190,000 (factura)
- Crédito: 1,140,000 (pago neto)
- Crédito: 50,000 (nota crédito)
- Débito: 50,000 (comprobante reversión)
- Saldo Final: 0 (todo conciliado)

Cuenta 530535:
- Débito: 40,000 (en el pago)
- Crédito: 40,000 (comprobante reversión)
- Saldo Final: 0 (reversión completada)
```

---

## 🐛 SOLUCIÓN DE PROBLEMAS COMUNES

### Problema 1: "No se encontraron descuentos condicionados"
**Causa:** No existen apuntes en cuenta 530535 para el año seleccionado
**Solución:** 
- Verificar que existan pagos con descuentos registrados
- Verificar que la cuenta sea exactamente `530535`
- Verificar que los pagos estén en diarios de tipo "banco"

### Problema 2: "Debe seleccionar un diario para los comprobantes"
**Causa:** No se seleccionó el diario de reversión
**Solución:** 
- Crear un diario de tipo "General" si no existe
- Seleccionarlo en el campo correspondiente

### Problema 3: Facturas no aparecen en la lista
**Causa:** Facturas ya procesadas o sin conciliación
**Solución:**
- Verificar que las facturas estén conciliadas con los pagos
- Verificar que no tengan notas crédito previas del sistema

### Problema 4: Error de conciliación
**Causa:** Cuentas no conciliables o montos no coinciden
**Solución:**
- Verificar que la cuenta CXC sea de tipo "Por Cobrar"
- Verificar configuración de la cuenta

### Problema 5: "No se encontró cuenta de ingresos"
**Causa:** La factura no tiene líneas de ingreso válidas
**Solución:**
- Revisar las líneas de la factura original
- Asegurar que tenga productos/servicios con cuenta de ingresos

---

## 📊 MÉTRICAS DE ÉXITO

### Validación de Proceso Exitoso

✅ **Documentos Creados:**
- 1 Nota Crédito por cada factura procesada
- 1 Comprobante de Reversión por cada factura procesada

✅ **Conciliación:**
- Todas las notas crédito conciliadas con su comprobante

✅ **Marcación:**
- Todas las NC tienen `is_conditional_discount_credit_note = True`

✅ **Reporte:**
- Excel generado con toda la información
- Sin errores en las columnas de estado

✅ **Balance:**
- Cuenta 530535 con saldo 0 (reversión completa)
- CXC totalmente conciliadas

---

## 📞 SOPORTE

Para problemas adicionales:
1. Revisar logs de Odoo: `/var/log/odoo/odoo-server.log`
2. Verificar permisos de usuario en Contabilidad
3. Contactar al equipo de desarrollo de LOGYCA

---

## 📝 CHECKLIST DE INSTALACIÓN

- [ ] Módulo copiado a directorio addons
- [ ] Permisos establecidos correctamente
- [ ] Odoo reiniciado
- [ ] Módulo instalado desde interfaz
- [ ] Menú visible en Contabilidad
- [ ] Cuenta 530535 existe
- [ ] Diario de reversión creado
- [ ] Usuario con permisos de contabilidad
- [ ] Prueba funcional completada
- [ ] Documentos generados correctamente
- [ ] Conciliación verificada
- [ ] Reporte Excel descargado y verificado

---

**Versión del documento:** 1.0.0
**Fecha:** Diciembre 2024
**Autor:** LOGYCA
