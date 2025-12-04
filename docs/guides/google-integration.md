# Google Integration Guide

Integrate with Google Workspace APIs.

## Supported Services

| Service | Nodes | Description |
|---------|-------|-------------|
| Gmail | 19 | Send, receive, search emails |
| Sheets | 18 | Read, write spreadsheets |
| Drive | 15 | Upload, download, manage files |
| Docs | 10 | Create, edit documents |
| Calendar | 12 | Manage events, calendars |

## Authentication

### OAuth 2.0 Setup

1. Create Google Cloud project
2. Enable required APIs
3. Create OAuth credentials
4. Configure redirect URI

### Credential Nodes

Use credential tab properties:

| Property | Description |
|----------|-------------|
| credential_name | Saved credential reference |
| oauth_token | OAuth access token |

## Gmail Nodes

### Send Email

| Node | Purpose |
|------|---------|
| GmailSendEmailNode | Send email |
| GmailSendWithAttachmentNode | Send with attachments |
| GmailReplyToEmailNode | Reply to thread |

### Read Email

| Node | Purpose |
|------|---------|
| GmailListEmailsNode | List inbox |
| GmailSearchEmailsNode | Search emails |
| GmailGetEmailNode | Get email details |

## Sheets Nodes

### Read Data

| Node | Purpose |
|------|---------|
| SheetsGetRangeNode | Get cell range |
| SheetsGetCellNode | Get single cell |

### Write Data

| Node | Purpose |
|------|---------|
| SheetsWriteRangeNode | Write to range |
| SheetsAppendRowNode | Add new row |

## Related Nodes

- [Google Nodes](../nodes/google/index.md)
- [Gmail Nodes](../nodes/google/gmail/index.md)
- [Sheets Nodes](../nodes/google/sheets/index.md)
