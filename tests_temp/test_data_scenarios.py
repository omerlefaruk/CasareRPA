import pytest
import asyncio
from casare_rpa.core.types import NodeStatus
from casare_rpa.nodes.data_operation_nodes import (
    JsonParseNode,
    GetPropertyNode,
    ListGetItemNode,
    MathOperationNode,
    FormatStringNode,
    RegexMatchNode,
    RegexReplaceNode,
    ConcatenateNode
)

class TestDataScenarios:
    @pytest.mark.asyncio
    async def test_order_processing_scenario(self):
        """
        Scenario: Process an order from a JSON response.
        1. Parse JSON response
        2. Extract order items and tax rate
        3. Get the first item
        4. Get item price
        5. Calculate tax amount
        6. Calculate total price
        7. Format output message
        """
        # 1. Parse JSON
        json_node = JsonParseNode("json_node")
        json_input = '{"order_id": "ORD-123", "items": [{"name": "Widget", "price": 50.0}, {"name": "Gadget", "price": 20.0}], "tax_rate": 0.1}'
        json_node.set_input_value("json_string", json_input)
        await json_node.execute(None)
        data = json_node.get_output_value("data")
        
        # 2. Extract items and tax rate
        get_items_node = GetPropertyNode("get_items")
        get_items_node.set_input_value("object", data)
        get_items_node.set_input_value("property_path", "items")
        await get_items_node.execute(None)
        items = get_items_node.get_output_value("value")
        
        get_tax_node = GetPropertyNode("get_tax")
        get_tax_node.set_input_value("object", data)
        get_tax_node.set_input_value("property_path", "tax_rate")
        await get_tax_node.execute(None)
        tax_rate = get_tax_node.get_output_value("value")
        
        # 3. Get first item
        get_item_node = ListGetItemNode("get_item")
        get_item_node.set_input_value("list", items)
        get_item_node.set_input_value("index", 0)
        await get_item_node.execute(None)
        first_item = get_item_node.get_output_value("item")
        
        # 4. Get item price
        get_price_node = GetPropertyNode("get_price")
        get_price_node.set_input_value("object", first_item)
        get_price_node.set_input_value("property_path", "price")
        await get_price_node.execute(None)
        price = get_price_node.get_output_value("value")
        
        # 5. Calculate tax amount (price * tax_rate)
        calc_tax_node = MathOperationNode("calc_tax", {"operation": "multiply"})
        calc_tax_node.set_input_value("a", price)
        calc_tax_node.set_input_value("b", tax_rate)
        await calc_tax_node.execute(None)
        tax_amount = calc_tax_node.get_output_value("result")
        
        # 6. Calculate total (price + tax_amount)
        calc_total_node = MathOperationNode("calc_total", {"operation": "add"})
        calc_total_node.set_input_value("a", price)
        calc_total_node.set_input_value("b", tax_amount)
        await calc_total_node.execute(None)
        total = calc_total_node.get_output_value("result")
        
        # 7. Format output
        format_node = FormatStringNode("format_output")
        format_node.set_input_value("template", "Item: {item}, Total: ${total:.2f}")
        format_node.set_input_value("variables", {"item": first_item["name"], "total": total})
        await format_node.execute(None)
        result = format_node.get_output_value("result")
        
        assert result == "Item: Widget, Total: $55.00"

    @pytest.mark.asyncio
    async def test_text_cleaning_scenario(self):
        """
        Scenario: Clean and format a messy phone number.
        1. Extract phone number using Regex
        2. Remove non-digit characters
        3. Format into standard format
        """
        raw_text = "Contact customer support at (555) 123-4567 for assistance."
        
        # 1. Extract phone number pattern
        regex_node = RegexMatchNode("extract_phone")
        regex_node.set_input_value("text", raw_text)
        regex_node.set_input_value("pattern", r"\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}")
        await regex_node.execute(None)
        phone_match = regex_node.get_output_value("first_match")
        
        # 2. Remove non-digits (replace everything that is NOT a digit with empty string)
        clean_node = RegexReplaceNode("clean_phone")
        clean_node.set_input_value("text", phone_match)
        clean_node.set_input_value("pattern", r"\D") # \D matches non-digits
        clean_node.set_input_value("replacement", "")
        await clean_node.execute(None)
        digits = clean_node.get_output_value("result")
        
        # 3. Format manually using substring (simulated with regex replace for now as we don't have substring node yet)
        # Or better, use FormatStringNode if we split it.
        # Let's use RegexReplace to format it back to XXX-XXX-XXXX
        format_phone_node = RegexReplaceNode("format_phone")
        format_phone_node.set_input_value("text", digits)
        format_phone_node.set_input_value("pattern", r"(\d{3})(\d{3})(\d{4})")
        format_phone_node.set_input_value("replacement", r"\1-\2-\3")
        await format_phone_node.execute(None)
        formatted_phone = format_phone_node.get_output_value("result")
        
        assert formatted_phone == "555-123-4567"
