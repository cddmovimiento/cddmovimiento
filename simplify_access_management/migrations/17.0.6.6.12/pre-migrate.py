from odoo.tools.sql import column_exists, rename_column
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        DELETE 
        FROM access_management_menu_rel_ah;
    """)
    _logger.info("Updated %s account moves", cr.rowcount)