# -*- coding: utf-8 -*-
# pre-migration script para renombrar columnas en logyca_payment_information sin perder datos

def migrate(cr, version):
    """
    Renombra las columnas 'move_name' a 'ref' y 'amount_total' a 'amount' en la tabla logyca_payment_information
    """
    # Renombrar move_name a ref si existe
    cr.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='logyca_payment_information' AND column_name='move_name';
    """)
    if cr.fetchone():
        cr.execute("""
            ALTER TABLE logyca_payment_information RENAME COLUMN move_name TO ref;
        """)
        print("Columna 'move_name' renombrada a 'ref'.")
        # Actualizar el campo en ir_model_fields para mantener consistencia en el ORM
        cr.execute("""
            UPDATE ir_model_fields
            SET name = 'ref'
            WHERE model = 'logyca.payment.information' AND name = 'move_name';
        """)
        # Actualizar las vistas que podrían estar utilizando el campo anterior
        cr.execute("""
            UPDATE ir_ui_view
            SET arch_db = replace(arch_db, 'move_name', 'ref')
            WHERE arch_db like '%move_name%' AND model = 'logyca.payment.information';
        """)
    else:
        print("La columna 'move_name' no existe o ya fue renombrada.")

    # Renombrar amount_total a amount si existe
    cr.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='logyca_payment_information' AND column_name='amount_total';
    """)
    if cr.fetchone():
        cr.execute("""
            ALTER TABLE logyca_payment_information RENAME COLUMN amount_total TO amount;
        """)
        print("Columna 'amount_total' renombrada a 'amount'.")
        # Actualizar el campo en ir_model_fields para mantener consistencia en el ORM
        cr.execute("""
            UPDATE ir_model_fields
            SET name = 'amount'
            WHERE model = 'logyca.payment.information' AND name = 'amount_total';
        """)
        # Actualizar las vistas que podrían estar utilizando el campo anterior
        cr.execute("""
            UPDATE ir_ui_view
            SET arch_db = replace(arch_db, 'amount_total', 'amount')
            WHERE arch_db like '%amount_total%' AND model = 'logyca.payment.information';
        """)
    else:
        print("La columna 'amount_total' no existe o ya fue renombrada.")
