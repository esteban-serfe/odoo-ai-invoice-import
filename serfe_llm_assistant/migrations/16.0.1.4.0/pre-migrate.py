def migrate(cr, version):
    """
    Pre-migration script to rename llm_prompt XML IDs to llm_assistant XML IDs
    to avoid conflicts during consolidation.
    """
    import logging

    _logger = logging.getLogger(__name__)

    _logger.info("Starting llm_prompt to llm_assistant XML ID migration")

    # Mapping of old llm_prompt XML IDs to new llm_assistant XML IDs
    xml_id_mappings = {
        # Tags
        "llm_prompt.tag_technical": "serfe_llm_assistant.tag_technical",
        "llm_prompt.tag_business": "serfe_llm_assistant.tag_business",
        "llm_prompt.tag_creative": "serfe_llm_assistant.tag_creative",
        "llm_prompt.tag_data": "serfe_llm_assistant.tag_data",
        "llm_prompt.tag_system": "serfe_llm_assistant.tag_system",
        "llm_prompt.tag_assistant": "serfe_llm_assistant.tag_assistant",
        # Categories
        "llm_prompt.category_general": "serfe_llm_assistant.category_general",
        "llm_prompt.category_technical": "serfe_llm_assistant.category_technical",
        "llm_prompt.category_business": "serfe_llm_assistant.category_business",
        "llm_prompt.category_creative": "serfe_llm_assistant.category_creative",
        # Export templates
        "llm_prompt.llm_prompt_export_template": "serfe_llm_assistant.llm_prompt_export_template",
        "llm_prompt.llm_prompt_export_line_name": "serfe_llm_assistant.llm_prompt_export_line_name",
        "llm_prompt.llm_prompt_export_line_description": "serfe_llm_assistant.llm_prompt_export_line_description",
        "llm_prompt.llm_prompt_export_line_active": "serfe_llm_assistant.llm_prompt_export_line_active",
        "llm_prompt.llm_prompt_export_line_category": "serfe_llm_assistant.llm_prompt_export_line_category",
        "llm_prompt.llm_prompt_export_line_tags": "serfe_llm_assistant.llm_prompt_export_line_tags",
        "llm_prompt.llm_prompt_export_line_template": "serfe_llm_assistant.llm_prompt_export_line_template",
        "llm_prompt.llm_prompt_export_line_format": "serfe_llm_assistant.llm_prompt_export_line_format",
        "llm_prompt.llm_prompt_export_line_arguments_json": "serfe_llm_assistant.llm_prompt_export_line_arguments_json",
        "llm_prompt.llm_prompt_export_line_example_args": "serfe_llm_assistant.llm_prompt_export_line_example_args",
        "llm_prompt.llm_prompt_category_export_template": "serfe_llm_assistant.llm_prompt_category_export_template",
        "llm_prompt.llm_prompt_category_export_line_name": "serfe_llm_assistant.llm_prompt_category_export_line_name",
        "llm_prompt.llm_prompt_category_export_line_code": "serfe_llm_assistant.llm_prompt_category_export_line_code",
        "llm_prompt.llm_prompt_category_export_line_parent": "serfe_llm_assistant.llm_prompt_category_export_line_parent",
        "llm_prompt.llm_prompt_category_export_line_description": "serfe_llm_assistant.llm_prompt_category_export_line_description",
        "llm_prompt.llm_prompt_category_export_line_sequence": "serfe_llm_assistant.llm_prompt_category_export_line_sequence",
        "llm_prompt.llm_prompt_tag_export_template": "serfe_llm_assistant.llm_prompt_tag_export_template",
        "llm_prompt.llm_prompt_tag_export_line_name": "serfe_llm_assistant.llm_prompt_tag_export_line_name",
        "llm_prompt.llm_prompt_tag_export_line_color": "serfe_llm_assistant.llm_prompt_tag_export_line_color",
    }

    # Update XML IDs in ir_model_data
    for old_xml_id, new_xml_id in xml_id_mappings.items():
        old_module, old_name = old_xml_id.split(".")
        new_module, new_name = new_xml_id.split(".")

        # Check if the old XML ID exists
        cr.execute(
            """
            SELECT id FROM ir_model_data
            WHERE module = %s AND name = %s
        """,
            (old_module, old_name),
        )

        if cr.fetchone():
            # Update the XML ID
            cr.execute(
                """
                UPDATE ir_model_data
                SET module = %s, name = %s
                WHERE module = %s AND name = %s
            """,
                (new_module, new_name, old_module, old_name),
            )

            _logger.info(f"Renamed XML ID: {old_xml_id} -> {new_xml_id}")

    _logger.info("Completed llm_prompt to llm_assistant XML ID migration")
