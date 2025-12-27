# Google Nodes Package Index

```xml<google_nodes_index>
  <!-- Google services integration nodes (Drive, Sheets, Docs, Gmail, Calendar). -->

  <files>
    <f>google_base.py</f>   <n>Base classes</n> <e>GoogleBaseNode, DriveBaseNode, SheetsBaseNode</e>
    <f>drive/</f>          <n>Google Drive</n> <e>DriveListFilesNode, DriveDownloadFileNode</e>
    <f>sheets/</f>         <n>Google Sheets</n> <e>SheetsGetCellNode, SheetsWriteCellNode</e>
    <f>docs/</f>           <n>Google Docs</n> <e>DocsGetTextNode, DocsInsertTextNode</e>
    <f>gmail/</f>          <n>Gmail</n> <e>GmailSendEmailNode, GmailListEmailsNode</e>
    <f>calendar/</f>       <n>Calendar</n> <e>CalendarListEventsNode, CalendarCreateEventNode</e>
  </files>

  <drive_list>
    <n>DriveListFilesNode</n>
    <d>List files in a Google Drive folder</d>
    <inputs>
      <i>folder_id</i>     <d>Folder to list (empty = all accessible files)</d>
      <i>query</i>         <d>Additional query filter (Drive API query syntax)</d>
      <i>mime_type</i>     <d>Filter by MIME type</d>
      <i>max_results</i>   <d>Maximum number of files to return</d>
      <i>order_by</i>      <d>Sort order</d>
      <i>include_trashed</i> <d>Include trashed files</d>
    </inputs>
    <outputs>
      <o>files</o>         <d>Array of file objects with id, name, mimeType, size</d>
      <o>file_count</o>    <d>Number of files returned</d>
      <o>has_more</o>      <d>Whether there are more results available</d>
      <o>folder_id</o>     <d>The folder ID being listed</d>
    </outputs>
  </drive_list>

  <drive_download>
    <n>DriveDownloadFileNode</n>
    <d>Download files from Google Drive. Supports single file and batch downloads</d>
    <modes>
      <m>Single file by ID: file_id + destination_path</m>
      <m>Single file object: file input (from ForEach) + destination_folder</m>
      <m>Batch download: files input (list) + destination_folder</m>
    </modes>
    <outputs>
      <o>file_path</o>     <d>Path to the downloaded file (single file mode)</d>
      <o>file_paths</o>    <d>List of downloaded file paths (batch mode)</d>
      <o>downloaded_count</o> <d>Number of files successfully downloaded</d>
    </outputs>
  </drive_download>

  <workflows>
    <w>Download all files from a folder</w>
      <p>DriveListFiles → DriveDownloadFile</p>
    </w>
    <w>Process files one by one with ForEach</w>
      <p>DriveListFiles → ForLoopStart → DriveDownloadFile</p>
    </w>
  </workflows>

  <entry_points>
    <code>
# Import Drive nodes
from casare_rpa.nodes.google import (
    DriveListFilesNode, DriveDownloadFileNode, DriveUploadFileNode
)

# Import Sheets nodes
from casare_rpa.nodes.google import (
    SheetsGetCellNode, SheetsWriteCellNode
)
    </code>
  </entry_points>
</google_nodes_index>
```
