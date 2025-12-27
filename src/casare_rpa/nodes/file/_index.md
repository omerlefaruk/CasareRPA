# File Nodes Package Index

```xml<file_nodes_index>
  <!-- File system operations: read, write, copy, move, delete, and image processing. -->

  <files>
    <f>file_read_nodes.py</f>    <n>Read file contents</n>          <e>ReadFileNode</e>
    <f>file_write_nodes.py</f>   <n>Write/append files</n>         <e>WriteFileNode, AppendFileNode</e>
    <f>file_system_nodes.py</f>  <n>File operations</n>            <e>CopyFileNode, MoveFileNode, DeleteFileNode</e>
    <f>directory_nodes.py</f>    <n>Directory operations</n>       <e>CreateDirectoryNode, ListFilesNode</e>
    <f>path_nodes.py</f>         <n>Path information</n>          <e>FileExistsNode, GetFileInfoNode</e>
    <f>structured_data.py</f>    <n>CSV, JSON, ZIP</n>             <e>ReadCSVNode, WriteJSONFileNode, ZipFilesNode</e>
    <f>image_nodes.py</f>        <n>Image processing</n>          <e>ImageConvertNode</e>
  </files>

  <image_convert>
    <n>ImageConvertNode</n>
    <d>Convert images between formats (PNG, JPEG, BMP, GIF, WEBP, TIFF, ICO)</d>
    <inputs>
      <i>source_path</i>   <d>Path to the image to convert (required)</d>
      <i>output_path</i>   <d>Destination path (auto-generated if empty)</d>
      <i>output_format</i> <d>JPEG, PNG, BMP, GIF, WEBP, TIFF, ICO (default: JPEG)</d>
      <i>quality</i>       <d>Compression quality 1-100 for JPEG/WEBP (default: 85)</d>
      <i>overwrite</i>     <d>Overwrite existing file (default: false)</d>
    </inputs>
    <outputs>
      <o>output_path</o>   <d>Path to the converted image</d>
      <o>success</o>       <d>Boolean</d>
      <o>error</o>         <d>Error message if failed</d>
    </outputs>
  </image_convert>

  <entry_points>
    <code>
from casare_rpa.nodes.file import (
    ReadFileNode, WriteFileNode, CopyFileNode,
    MoveFileNode, DeleteFileNode, ListFilesNode,
    ImageConvertNode,
)
    </code>
  </entry_points>

  <security>
    <p>All file nodes validate paths against security rules</p>
    <p>System directories blocked by default</p>
    <p>Use allow_dangerous_paths=True to override (use with caution)</p>
  </security>
</file_nodes_index>
```
