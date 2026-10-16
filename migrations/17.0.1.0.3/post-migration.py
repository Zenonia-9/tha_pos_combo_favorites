def migrate(cr, version):
    """Preserve existing nested choices while switching to independent relations."""
    cr.execute("""
        INSERT INTO pos_combo_choice_rel (parent_id, child_id)
        SELECT tha_parent_combo_id, id
          FROM pos_combo
         WHERE tha_parent_combo_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)
    cr.execute("UPDATE pos_combo SET tha_parent_combo_id = NULL WHERE tha_parent_combo_id IS NOT NULL")
