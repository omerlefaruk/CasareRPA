# Implement Node Command

Workflow for implementing new nodes.

## Prerequisites
- Node requirements defined
- Checked `_NODE_REGISTRY` for existing nodes

## Steps

### 1. Search
- [ ] Check `nodes/_index.md`
- [ ] Search existing nodes
- [ ] Confirm new node needed

### 2. Create Node File
Location: `nodes/{category}/{node_name}.py`

### 3. Implement Node
```python
@node_schema(
    PropertyDef("prop", PropertyType.STRING, essential=True),
)
@executable_node
class MyNode(BaseNode):
    NODE_NAME = "My Node"

    async def execute(self, context):
        return {"result": value}
```

### 4. Register
Add to `_NODE_REGISTRY` in `nodes/__init__.py`

### 5. Create Visual Node
In `presentation/canvas/visual_nodes/`

### 6. Test
Create `tests/nodes/test_{node_name}.py`

### 7. Document
Update `nodes/_index.md`
