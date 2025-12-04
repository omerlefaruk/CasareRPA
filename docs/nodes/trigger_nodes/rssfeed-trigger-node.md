# RSSFeedTriggerNode

RSS Feed trigger node that fires when new items are published.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.rss_feed_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\rss_feed_trigger_node.py:71`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `item` | DICT | RSS Item |
| `title` | STRING | Title |
| `link` | STRING | Link |
| `description` | STRING | Description |
| `published` | STRING | Published Date |
| `author` | STRING | Author |
| `categories` | LIST | Categories |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `feed_url` | STRING | `-` | Yes | URL of the RSS/Atom feed |
| `poll_interval_minutes` | INTEGER | `15` | No | How often to check for new items |
| `filter_keywords` | STRING | `` | No | Comma-separated keywords to filter items |
| `filter_mode` | CHOICE | `any` | No | Match any/all/none of the keywords Choices: any, all, none |
| `max_items_per_check` | INTEGER | `10` | No | Maximum items to process per poll |
| `include_description` | BOOLEAN | `True` | No | Include full description in output |

## Inheritance

Extends: `BaseTriggerNode`
