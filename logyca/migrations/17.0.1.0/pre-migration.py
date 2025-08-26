# -*- coding: utf-8 -*-
# pre-migration script for renaming 'date_payment' to 'date' in logyca.payment.information

def migrate(cr, version):
    """
    Renombra la columna 'date_payment' a 'date' en la tabla logyca_payment_information
    """
    cr.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='logyca_payment_information' AND column_name='date_payment';
    """)
    if cr.fetchone():
        cr.execute("""
            ALTER TABLE logyca_payment_information RENAME COLUMN date_payment TO date;
        """)
        print("Columna 'date_payment' renombrada a 'date' exitosamente.")
    else:
        print("La columna 'date_payment' no existe o ya fue renombrada.")
