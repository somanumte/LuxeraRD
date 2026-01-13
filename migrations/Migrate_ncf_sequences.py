# ============================================
# MIGRACIÓN: Sistema de NCF con Secuencias Independientes
# ============================================
# Este script debe ejecutarse UNA SOLA VEZ para:
# 1. Crear la tabla ncf_sequences
# 2. Agregar el campo ncf_type a invoices
# 3. Migrar datos existentes
#
# Ejecución: python migrations/migrate_ncf_sequences.py
# O desde flask shell: exec(open('migrations/migrate_ncf_sequences.py').read())
# ============================================

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text, inspect
from datetime import date, timedelta

# Crear aplicación
app = create_app('default')

# Definición de tipos de NCF
NCF_TYPES = {
    'B01': {'name': 'Crédito Fiscal', 'category': 'ventas'},
    'B02': {'name': 'Consumo', 'category': 'ventas'},
    'B03': {'name': 'Nota de Débito', 'category': 'ventas'},
    'B04': {'name': 'Nota de Crédito', 'category': 'ventas'},
    'B11': {'name': 'Compras (Proveedores Informales)', 'category': 'gastos'},
    'B12': {'name': 'Gastos Menores', 'category': 'gastos'},
    'B13': {'name': 'Pagos al Exterior', 'category': 'gastos'},
    'B14': {'name': 'Regímenes Especiales', 'category': 'ventas'},
    'B15': {'name': 'Gubernamental', 'category': 'ventas'},
    'B16': {'name': 'Exportaciones', 'category': 'ventas'},
}

NCF_SALES_TYPES = ['B01', 'B02', 'B03', 'B04', 'B14', 'B15', 'B16']


def table_exists(table_name):
    """Verifica si una tabla existe en la base de datos"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """Verifica si una columna existe en una tabla"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate():
    """Ejecuta la migración completa"""

    print("\n" + "=" * 60)
    print("🔄 MIGRACIÓN: Sistema NCF con Secuencias Independientes")
    print("=" * 60)

    with app.app_context():

        # ==========================================
        # PASO 1: Crear tabla ncf_sequences
        # ==========================================
        print("\n📋 Paso 1: Verificando tabla ncf_sequences...")

        if table_exists('ncf_sequences'):
            print("   ✓ La tabla ncf_sequences ya existe")
        else:
            print("   → Creando tabla ncf_sequences...")

            create_table_sql = """
                               CREATE TABLE ncf_sequences \
                               ( \
                                   id               INTEGER PRIMARY KEY AUTOINCREMENT, \
                                   ncf_type         VARCHAR(3)   NOT NULL UNIQUE, \
                                   name             VARCHAR(100) NOT NULL, \
                                   current_sequence INTEGER      NOT NULL DEFAULT 1, \
                                   range_start      INTEGER      NOT NULL DEFAULT 1, \
                                   range_end        INTEGER, \
                                   valid_until      DATE, \
                                   is_active        BOOLEAN      NOT NULL DEFAULT 1, \
                                   created_at       DATETIME              DEFAULT CURRENT_TIMESTAMP, \
                                   updated_at       DATETIME              DEFAULT CURRENT_TIMESTAMP
                               ); \
                               """

            # Para PostgreSQL usar esta versión:
            create_table_sql_postgres = """
                                        CREATE TABLE ncf_sequences \
                                        ( \
                                            id               SERIAL PRIMARY KEY, \
                                            ncf_type         VARCHAR(3)   NOT NULL UNIQUE, \
                                            name             VARCHAR(100) NOT NULL, \
                                            current_sequence INTEGER      NOT NULL DEFAULT 1, \
                                            range_start      INTEGER      NOT NULL DEFAULT 1, \
                                            range_end        INTEGER, \
                                            valid_until      DATE, \
                                            is_active        BOOLEAN      NOT NULL DEFAULT TRUE, \
                                            created_at       TIMESTAMP             DEFAULT CURRENT_TIMESTAMP, \
                                            updated_at       TIMESTAMP             DEFAULT CURRENT_TIMESTAMP
                                        ); \
                                        """

            try:
                # Intentar primero con SQLite syntax
                db.session.execute(text(create_table_sql))
                db.session.commit()
                print("   ✓ Tabla ncf_sequences creada exitosamente (SQLite)")
            except Exception as e:
                db.session.rollback()
                try:
                    # Intentar con PostgreSQL syntax
                    db.session.execute(text(create_table_sql_postgres))
                    db.session.commit()
                    print("   ✓ Tabla ncf_sequences creada exitosamente (PostgreSQL)")
                except Exception as e2:
                    print(f"   ✗ Error creando tabla: {e2}")
                    return False

        # ==========================================
        # PASO 2: Agregar columna ncf_type a invoices
        # ==========================================
        print("\n📋 Paso 2: Verificando columna ncf_type en invoices...")

        if column_exists('invoices', 'ncf_type'):
            print("   ✓ La columna ncf_type ya existe en invoices")
        else:
            print("   → Agregando columna ncf_type a invoices...")

            try:
                db.session.execute(text(
                    "ALTER TABLE invoices ADD COLUMN ncf_type VARCHAR(3) DEFAULT 'B02'"
                ))
                db.session.commit()
                print("   ✓ Columna ncf_type agregada exitosamente")
            except Exception as e:
                db.session.rollback()
                print(f"   ✗ Error agregando columna: {e}")
                return False

        # ==========================================
        # PASO 3: Crear índice para ncf_type
        # ==========================================
        print("\n📋 Paso 3: Creando índice para ncf_type...")

        try:
            db.session.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_invoice_ncf_type ON invoices(ncf_type)"
            ))
            db.session.commit()
            print("   ✓ Índice creado exitosamente")
        except Exception as e:
            # El índice puede ya existir, no es crítico
            db.session.rollback()
            print(f"   ⚠ Índice ya existe o no se pudo crear: {e}")

        # ==========================================
        # PASO 4: Migrar datos de facturas existentes
        # ==========================================
        print("\n📋 Paso 4: Migrando datos de facturas existentes...")

        try:
            # Actualizar ncf_type basándose en el prefijo del NCF existente
            result = db.session.execute(text("""
                                             UPDATE invoices
                                             SET ncf_type = SUBSTR(ncf, 1, 3)
                                             WHERE ncf IS NOT NULL
                                                 AND LENGTH(ncf) >= 3
                                                 AND ncf_type IS NULL
                                                OR ncf_type = ''
                                             """))
            db.session.commit()

            # Contar cuántas se actualizaron
            count_result = db.session.execute(text(
                "SELECT COUNT(*) FROM invoices WHERE ncf_type IS NOT NULL AND ncf_type != ''"
            )).scalar()

            print(f"   ✓ {count_result} facturas con ncf_type asignado")
        except Exception as e:
            db.session.rollback()
            print(f"   ⚠ Error migrando datos (puede ser normal si no hay facturas): {e}")

        # ==========================================
        # PASO 5: Inicializar secuencias de NCF
        # ==========================================
        print("\n📋 Paso 5: Inicializando secuencias de NCF...")

        # Fecha de vencimiento por defecto (2 años)
        default_valid_until = date.today() + timedelta(days=730)

        for ncf_type, info in NCF_TYPES.items():
            try:
                # Verificar si ya existe
                exists = db.session.execute(text(
                    "SELECT COUNT(*) FROM ncf_sequences WHERE ncf_type = :ncf_type"
                ), {'ncf_type': ncf_type}).scalar()

                if exists > 0:
                    print(f"   ✓ Secuencia {ncf_type} ya existe")
                    continue

                # Buscar el máximo NCF usado de este tipo en facturas existentes
                max_seq_result = db.session.execute(text("""
                                                         SELECT MAX(CAST(SUBSTR(ncf, 4, 8) AS INTEGER))
                                                         FROM invoices
                                                         WHERE ncf LIKE :pattern
                                                         """), {'pattern': f'{ncf_type}%'}).scalar()

                # Si hay facturas existentes, comenzar desde el siguiente
                current_seq = (max_seq_result or 0) + 1

                # Insertar nueva secuencia
                db.session.execute(text("""
                                        INSERT INTO ncf_sequences (ncf_type, name, current_sequence, range_start,
                                                                   range_end, valid_until, is_active)
                                        VALUES (:ncf_type, :name, :current_seq, 1, 99999999, :valid_until, 1)
                                        """), {
                                       'ncf_type': ncf_type,
                                       'name': info['name'],
                                       'current_seq': current_seq,
                                       'valid_until': default_valid_until.isoformat()
                                   })
                db.session.commit()

                print(f"   ✓ Secuencia {ncf_type} ({info['name']}) creada - Inicio: {current_seq}")

            except Exception as e:
                db.session.rollback()
                print(f"   ⚠ Error con secuencia {ncf_type}: {e}")

        # ==========================================
        # PASO 6: Verificación final
        # ==========================================
        print("\n📋 Paso 6: Verificación final...")

        try:
            # Contar secuencias
            seq_count = db.session.execute(text(
                "SELECT COUNT(*) FROM ncf_sequences"
            )).scalar()

            # Contar facturas con ncf_type
            inv_count = db.session.execute(text(
                "SELECT COUNT(*) FROM invoices WHERE ncf_type IS NOT NULL"
            )).scalar()

            # Mostrar secuencias creadas
            sequences = db.session.execute(text("""
                                                SELECT ncf_type, name, current_sequence, valid_until, is_active
                                                FROM ncf_sequences
                                                ORDER BY ncf_type
                                                """)).fetchall()

            print(f"\n   📊 Resumen:")
            print(f"   • Secuencias NCF creadas: {seq_count}")
            print(f"   • Facturas con ncf_type: {inv_count}")

            print(f"\n   📋 Detalle de secuencias:")
            print(f"   {'Tipo':<5} {'Nombre':<35} {'Secuencia':<12} {'Vence':<12} {'Activo'}")
            print(f"   {'-' * 5} {'-' * 35} {'-' * 12} {'-' * 12} {'-' * 6}")

            for seq in sequences:
                ncf_type, name, current_seq, valid_until, is_active = seq
                active_str = "✓" if is_active else "✗"
                valid_str = str(valid_until) if valid_until else "Sin fecha"
                print(f"   {ncf_type:<5} {name:<35} {current_seq:<12} {valid_str:<12} {active_str}")

        except Exception as e:
            print(f"   ⚠ Error en verificación: {e}")

        print("\n" + "=" * 60)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("\n💡 Próximos pasos:")
        print("   1. Reinicia la aplicación Flask")
        print("   2. Ve a Facturas > Configuración para ajustar secuencias")
        print("   3. Actualiza las fechas de vencimiento según tu autorización DGII")
        print("\n")

        return True


def rollback():
    """Revierte la migración (usar con precaución)"""

    print("\n" + "=" * 60)
    print("⚠️  ROLLBACK: Revirtiendo migración NCF")
    print("=" * 60)

    confirm = input("\n¿Estás seguro? Esto eliminará la tabla ncf_sequences. (escribir 'SI'): ")

    if confirm != 'SI':
        print("Rollback cancelado.")
        return

    with app.app_context():
        try:
            # Eliminar tabla ncf_sequences
            db.session.execute(text("DROP TABLE IF EXISTS ncf_sequences"))
            db.session.commit()
            print("✓ Tabla ncf_sequences eliminada")

            # Nota: No eliminamos la columna ncf_type porque SQLite no soporta DROP COLUMN
            # y los datos son útiles mantenerlos
            print("⚠ La columna ncf_type en invoices se mantiene (contiene datos históricos)")

            print("\n✅ Rollback completado")

        except Exception as e:
            db.session.rollback()
            print(f"✗ Error en rollback: {e}")


def show_status():
    """Muestra el estado actual de las secuencias NCF"""

    print("\n" + "=" * 60)
    print("📊 ESTADO ACTUAL DE SECUENCIAS NCF")
    print("=" * 60)

    with app.app_context():
        try:
            if not table_exists('ncf_sequences'):
                print("\n⚠ La tabla ncf_sequences no existe. Ejecute la migración primero.")
                return

            sequences = db.session.execute(text("""
                                                SELECT ncf_type,
                                                       name,
                                                       current_sequence,
                                                       range_start,
                                                       range_end,
                                                       valid_until,
                                                       is_active
                                                FROM ncf_sequences
                                                ORDER BY ncf_type
                                                """)).fetchall()

            if not sequences:
                print("\n⚠ No hay secuencias configuradas.")
                return

            print(f"\n{'Tipo':<5} {'Nombre':<30} {'Actual':<10} {'Rango':<20} {'Vence':<12} {'Estado'}")
            print("-" * 95)

            for seq in sequences:
                ncf_type, name, current_seq, range_start, range_end, valid_until, is_active = seq

                # Calcular estado
                if not is_active:
                    status = "❌ Inactivo"
                elif valid_until and date.fromisoformat(str(valid_until)) < date.today():
                    status = "⚠️ Vencido"
                elif range_end and current_seq > range_end:
                    status = "⚠️ Agotado"
                else:
                    status = "✅ Activo"

                range_str = f"{range_start}-{range_end if range_end else '∞'}"
                valid_str = str(valid_until) if valid_until else "Sin fecha"

                # Próximo NCF
                next_ncf = f"{ncf_type}{str(current_seq).zfill(8)}"

                print(f"{ncf_type:<5} {name:<30} {current_seq:<10} {range_str:<20} {valid_str:<12} {status}")
                print(f"      Próximo NCF: {next_ncf}")
                print()

            # Estadísticas de facturas
            print("-" * 95)
            print("\n📈 Facturas por tipo de NCF:")

            stats = db.session.execute(text("""
                                            SELECT ncf_type,
                                                   COUNT(*) as count, 
                       SUM(total) as total_amount
                                            FROM invoices
                                            WHERE ncf_type IS NOT NULL
                                            GROUP BY ncf_type
                                            ORDER BY ncf_type
                                            """)).fetchall()

            for stat in stats:
                ncf_type, count, total = stat
                total_fmt = f"RD$ {float(total or 0):,.2f}"
                print(f"   {ncf_type}: {count} facturas - {total_fmt}")

        except Exception as e:
            print(f"\n✗ Error: {e}")


# ==========================================
# PUNTO DE ENTRADA
# ==========================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migración de NCF con secuencias independientes')
    parser.add_argument('--rollback', action='store_true', help='Revertir la migración')
    parser.add_argument('--status', action='store_true', help='Mostrar estado actual')

    args = parser.parse_args()

    if args.rollback:
        rollback()
    elif args.status:
        show_status()
    else:
        migrate()