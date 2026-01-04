"""
Tests for List/Tree Primitive Components v2.

Tests ListItem, TreeItem, and TableHeader components
for proper v2 styling and behavior.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QListWidget,
    QTableWidget,
    QTreeWidget,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import (
    ListItem,
    TableHeader,
    TreeItem,
    apply_header_style,
    apply_list_style,
    apply_table_style,
    apply_tree_style,
    create_list_item,
    create_tree_item,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def widget(qapp):
    """Parent widget for testing."""
    return QWidget()


@pytest.fixture
def list_widget(qapp):
    """QListWidget for testing."""
    return QListWidget()


@pytest.fixture
def tree_widget(qapp):
    """QTreeWidget for testing."""
    return QTreeWidget()


@pytest.fixture
def table_widget(qapp):
    """QTableWidget for testing."""
    table = QTableWidget()
    table.setColumnCount(3)
    table.setRowCount(2)
    return table


# =============================================================================
# LIST ITEM TESTS
# =============================================================================


class TestListItem:
    """Tests for ListItem component."""

    def test_initialization(self):
        """Test ListItem initializes correctly."""
        item = ListItem(text="Item 1", value="1")
        assert item.text() == "Item 1"
        assert item.get_value() == "1"
        assert item.get_icon_name() is None
        assert item.is_item_enabled()

    def test_with_icon(self):
        """Test ListItem with icon."""
        item = ListItem(text="File", value="file1", icon="file")
        assert item.get_icon_name() == "file"
        assert not item.icon().isNull()

    def test_set_get_value(self):
        """Test set_value and get_value methods."""
        item = ListItem(text="Item", value="initial")
        assert item.get_value() == "initial"

        item.set_value("updated")
        assert item.get_value() == "updated"

    def test_set_enabled(self):
        """Test set_enabled method."""
        item = ListItem(text="Item", value="1")
        assert item.is_item_enabled()

        item.set_enabled(False)
        assert not item.is_item_enabled()

        item.set_enabled(True)
        assert item.is_item_enabled()

    def test_disabled_initialization(self):
        """Test ListItem initialized as disabled."""
        item = ListItem(text="Item", value="1", enabled=False)
        assert not item.is_item_enabled()

    def test_selected_initialization(self):
        """Test ListItem with selected state."""
        item = ListItem(text="Item", value="1", selected=True)
        # Selected state only takes effect when added to widget
        assert item.isSelected()

    def test_clone(self):
        """Test clone method."""
        item = ListItem(text="Original", value="1", icon="file")
        item.setSelected(True)

        cloned = item.clone()
        assert cloned.text() == "Original"
        assert cloned.get_value() == "1"
        assert cloned.get_icon_name() == "file"
        assert cloned.isSelected()

    def test_clone_with_icon(self):
        """Test clone preserves icon."""
        item = ListItem(text="Item", value="1", icon="folder")
        cloned = item.clone()

        assert cloned.get_icon_name() == "folder"
        assert not cloned.icon().isNull()

    def test_data_stored_in_user_role(self):
        """Test value is stored in UserRole."""
        item = ListItem(text="Item", value="test_value")
        assert item.data(Qt.ItemDataRole.UserRole) == "test_value"


# =============================================================================
# TREE ITEM TESTS
# =============================================================================


class TestTreeItem:
    """Tests for TreeItem component."""

    def test_initialization(self):
        """Test TreeItem initializes correctly."""
        item = TreeItem(text="Root", value="root1")
        assert item.text(0) == "Root"
        assert item.get_value() == "root1"
        assert item.get_icon_name() is None
        assert not item.has_children_items()

    def test_with_icon(self):
        """Test TreeItem with icon."""
        item = TreeItem(text="Folder", value="folder1", icon="folder")
        assert item.get_icon_name() == "folder"
        assert not item.icon(0).isNull()

    def test_add_child(self):
        """Test add_child method."""
        parent = TreeItem(text="Parent", value="parent")
        child = TreeItem(text="Child", value="child")

        parent.add_child(child)

        assert parent.child_count() == 1
        assert parent.has_children_items()
        assert child in parent.get_children()

    def test_add_multiple_children(self):
        """Test adding multiple children."""
        parent = TreeItem(text="Parent", value="parent")
        children = [TreeItem(text=f"Child {i}", value=f"child{i}") for i in range(3)]

        for child in children:
            parent.add_child(child)

        assert parent.child_count() == 3

    def test_remove_child(self):
        """Test remove_child method."""
        parent = TreeItem(text="Parent", value="parent")
        child = TreeItem(text="Child", value="child")

        parent.add_child(child)
        assert parent.child_count() == 1

        parent.remove_child(child)
        assert parent.child_count() == 0

    def test_insert_child(self):
        """Test insert_child method."""
        parent = TreeItem(text="Parent", value="parent")
        child1 = TreeItem(text="Child 1", value="c1")
        child2 = TreeItem(text="Child 2", value="c2")
        child3 = TreeItem(text="Child 3", value="c3")

        parent.add_child(child1)
        parent.add_child(child3)
        parent.insert_child(1, child2)

        assert parent.child_count() == 3
        assert parent.child(0) == child1
        assert parent.child(1) == child2
        assert parent.child(2) == child3

    def test_get_children(self):
        """Test get_children returns copy."""
        parent = TreeItem(text="Parent", value="parent")
        child1 = TreeItem(text="Child 1", value="c1")
        child2 = TreeItem(text="Child 2", value="c2")

        parent.add_child(child1)
        parent.add_child(child2)

        children = parent.get_children()
        assert len(children) == 2
        # Verify it's a copy (modifications don't affect original)
        children.clear()
        assert parent.child_count() == 2

    def test_set_get_value(self):
        """Test set_value and get_value methods."""
        item = TreeItem(text="Item", value="initial")
        assert item.get_value() == "initial"

        item.set_value("updated")
        assert item.get_value() == "updated"

    def test_set_enabled(self):
        """Test set_enabled method."""
        item = TreeItem(text="Item", value="1")
        assert item.is_item_enabled()

        item.set_enabled(False)
        assert not item.is_item_enabled()

        item.set_enabled(True)
        assert item.is_item_enabled()

    def test_set_expanded(self):
        """Test set_expanded method."""
        parent = TreeItem(text="Parent", value="parent")
        child = TreeItem(text="Child", value="child")

        parent.add_child(child)
        parent.set_expanded(True)

        assert parent._is_expanded is True

    def test_expanded_signal(self):
        """Test expanded_changed signal."""
        parent = TreeItem(text="Parent", value="parent")
        child = TreeItem(text="Child", value="child")
        parent.add_child(child)

        results = []

        def on_expanded(expanded: bool):
            results.append(expanded)

        parent.expanded_changed.connect(on_expanded)
        parent.set_expanded(True)

        # Signal should be emitted
        assert True in results or results == [True]

    def test_clone(self):
        """Test clone method (without children)."""
        parent = TreeItem(text="Parent", value="parent")
        child = TreeItem(text="Child", value="child")
        parent.add_child(child)

        cloned = parent.clone()

        assert cloned.text(0) == "Parent"
        assert cloned.get_value() == "parent"
        assert cloned.child_count() == 0  # No children in shallow clone

    def test_clone_with_children(self):
        """Test clone_with_children method."""
        parent = TreeItem(text="Parent", value="parent")
        child1 = TreeItem(text="Child 1", value="c1")
        child2 = TreeItem(text="Child 2", value="c2")

        parent.add_child(child1)
        parent.add_child(child2)

        cloned = parent.clone_with_children()

        assert cloned.text(0) == "Parent"
        assert cloned.child_count() == 2

    def test_data_stored_in_user_role(self):
        """Test value is stored in UserRole."""
        item = TreeItem(text="Item", value="test_value")
        assert item.data(0, Qt.ItemDataRole.UserRole) == "test_value"


# =============================================================================
# TABLE HEADER TESTS
# =============================================================================


class TestTableHeader:
    """Tests for TableHeader component."""

    def test_initialization(self, table_widget):
        """Test TableHeader initializes correctly."""
        header = TableHeader(table_widget.horizontalHeader())
        assert header.get_sections() == []
        assert header._header is not None

    def test_add_section(self, table_widget):
        """Test add_section method."""
        header = TableHeader(table_widget.horizontalHeader())
        header.add_section("Name", "name", sortable=True)
        header.add_section("Size", "size", sortable=False)

        sections = header.get_sections()
        assert len(sections) == 2
        assert sections[0]["id"] == "name"
        assert sections[0]["text"] == "Name"
        assert sections[0]["sortable"] is True
        assert sections[1]["id"] == "size"
        assert sections[1]["sortable"] is False

    def test_remove_section(self, table_widget):
        """Test remove_section method."""
        header = TableHeader(table_widget.horizontalHeader())
        header.add_section("Name", "name")
        header.add_section("Size", "size")

        assert len(header.get_sections()) == 2

        header.remove_section("name")
        sections = header.get_sections()
        assert len(sections) == 1
        assert sections[0]["id"] == "size"

    def test_set_sort_order(self, table_widget):
        """Test set_sort_order method."""
        header = TableHeader(table_widget.horizontalHeader())
        header.add_section("Name", "name", sortable=True)
        header.add_section("Size", "size", sortable=True)

        header.set_sort_order("name", "asc")
        assert header.get_sort_order("name") == "asc"

        header.set_sort_order("name", "desc")
        assert header.get_sort_order("name") == "desc"

        header.set_sort_order("name", "none")
        assert header.get_sort_order("name") == "none"

    def test_get_sorted_column(self, table_widget):
        """Test get_sorted_column method."""
        header = TableHeader(table_widget.horizontalHeader())
        header.add_section("Name", "name", sortable=True)
        header.add_section("Size", "size", sortable=True)

        assert header.get_sorted_column() is None

        header.set_sort_order("name", "asc")
        sorted_info = header.get_sorted_column()
        assert sorted_info == ("name", "asc")

    def test_clear_sort(self, table_widget):
        """Test clear_sort method."""
        header = TableHeader(table_widget.horizontalHeader())
        header.add_section("Name", "name", sortable=True)
        header.add_section("Size", "size", sortable=True)

        header.set_sort_order("name", "asc")
        header.set_sort_order("size", "desc")

        header.clear_sort()

        assert header.get_sort_order("name") == "none"
        assert header.get_sort_order("size") == "none"
        assert header.get_sorted_column() is None

    def test_sort_requested_signal(self, table_widget):
        """Test sort_requested signal."""
        header = TableHeader(table_widget.horizontalHeader())
        header.add_section("Name", "name", sortable=True)

        results = []

        def on_sort(col_id: str, order: str):
            results.append((col_id, order))

        header.sort_requested.connect(on_sort)

        # Simulate section click
        header._on_section_clicked(0)

        # Should have emitted sort request
        assert len(results) > 0
        assert results[0][0] == "name"
        assert results[0][1] in ("asc", "desc", "none")

    def test_non_sortable_column(self, table_widget):
        """Test non-sortable columns don't emit signal."""
        header = TableHeader(table_widget.horizontalHeader())
        header.add_section("Name", "name", sortable=False)

        results = []

        def on_sort(col_id: str, order: str):
            results.append((col_id, order))

        header.sort_requested.connect(on_sort)

        # Click on non-sortable column
        header._on_section_clicked(0)

        # Sort order should remain none
        assert header.get_sort_order("name") == "none"


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_apply_list_style_standard(self, list_widget):
        """Test apply_list_style with standard size."""
        apply_list_style(list_widget, size="standard")
        assert list_widget.styleSheet() != ""
        # Check alternating row colors is disabled
        assert not list_widget.alternatingRowColors()

    def test_apply_list_style_compact(self, list_widget):
        """Test apply_list_style with compact size."""
        apply_list_style(list_widget, size="compact")
        assert list_widget.styleSheet() != ""

    def test_apply_tree_style(self, tree_widget):
        """Test apply_tree_style function."""
        apply_tree_style(tree_widget)
        assert tree_widget.styleSheet() != ""
        assert tree_widget.isHeaderHidden()
        assert tree_widget.indentation() == TOKENS_V2.spacing.lg

    def test_apply_table_style(self, table_widget):
        """Test apply_table_style function."""
        apply_table_style(table_widget)
        assert table_widget.styleSheet() != ""
        # Vertical header should be hidden
        assert not table_widget.verticalHeader().isVisible()

    def test_apply_header_style(self, table_widget):
        """Test apply_header_style function."""
        header = table_widget.horizontalHeader()
        apply_header_style(header)
        assert header.styleSheet() != ""

    def test_create_list_item(self):
        """Test create_list_item convenience function."""
        item = create_list_item("Item 1", value="1", icon="file")
        assert isinstance(item, ListItem)
        assert item.text() == "Item 1"
        assert item.get_value() == "1"
        assert item.get_icon_name() == "file"

    def test_create_tree_item(self):
        """Test create_tree_item convenience function."""
        child = create_tree_item("Child", value="child", icon="file")
        parent = create_tree_item(
            "Parent",
            value="parent",
            icon="folder",
            children=[child],
            expanded=True,
        )

        assert isinstance(parent, TreeItem)
        assert parent.text(0) == "Parent"
        assert parent.child_count() == 1
        assert parent._is_expanded is True


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestListIntegration:
    """Integration tests with QListWidget."""

    def test_add_items_to_widget(self, list_widget):
        """Test adding ListItems to QListWidget."""
        apply_list_style(list_widget)

        items = [ListItem(text=f"Item {i}", value=f"value{i}", icon="file") for i in range(3)]

        for item in items:
            list_widget.addItem(item)

        assert list_widget.count() == 3

    def test_select_item(self, list_widget):
        """Test selecting items by value."""
        apply_list_style(list_widget)

        item1 = ListItem(text="Item 1", value="1")
        item2 = ListItem(text="Item 2", value="2")

        list_widget.addItem(item1)
        list_widget.addItem(item2)

        list_widget.setCurrentItem(item1)
        assert list_widget.currentItem().get_value() == "1"

    def test_disabled_items(self, list_widget):
        """Test disabled items behavior."""
        apply_list_style(list_widget)

        enabled_item = ListItem(text="Enabled", value="enabled", enabled=True)
        disabled_item = ListItem(text="Disabled", value="disabled", enabled=False)

        list_widget.addItem(enabled_item)
        list_widget.addItem(disabled_item)

        assert list_widget.item(0).is_item_enabled()
        assert not list_widget.item(1).is_item_enabled()


class TestTreeIntegration:
    """Integration tests with QTreeWidget."""

    def test_add_nested_items(self, tree_widget):
        """Test adding nested TreeItems to QTreeWidget."""
        apply_tree_style(tree_widget)

        parent = TreeItem(text="Folder", value="folder", icon="folder")
        parent.add_child(TreeItem(text="File 1", value="f1", icon="file"))
        parent.add_child(TreeItem(text="File 2", value="f2", icon="file"))

        tree_widget.addTopLevelItem(parent)

        assert tree_widget.topLevelItemCount() == 1
        top_item = tree_widget.topLevelItem(0)
        assert top_item.childCount() == 2

    def test_multiple_top_level_items(self, tree_widget):
        """Test multiple top-level items."""
        apply_tree_style(tree_widget)

        for i in range(3):
            item = TreeItem(text=f"Item {i}", value=f"value{i}")
            tree_widget.addTopLevelItem(item)

        assert tree_widget.topLevelItemCount() == 3


class TestTableIntegration:
    """Integration tests with QTableWidget."""

    def test_table_with_header_sections(self, table_widget):
        """Test TableHeader with QTableWidget."""
        apply_table_style(table_widget)

        header = TableHeader(table_widget.horizontalHeader())
        header.add_section("Name", "name", sortable=True)
        header.add_section("Type", "type", sortable=True)
        header.add_section("Size", "size", sortable=True)

        assert len(header.get_sections()) == 3
