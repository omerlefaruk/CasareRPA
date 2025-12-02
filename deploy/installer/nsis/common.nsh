; =============================================================================
; CasareRPA Common NSIS Macros and Definitions
; =============================================================================
; Include this file in all CasareRPA NSIS scripts for shared functionality.
;
; Usage:
;   !include "nsis\common.nsh"
;
; Provides:
;   - Common includes
;   - Version from environment or default
;   - Shared macros for registry, shortcuts, config
;   - Windows version checks
; =============================================================================

!ifndef CASARE_COMMON_INCLUDED
!define CASARE_COMMON_INCLUDED

; -----------------------------------------------------------------------------
; Standard Includes
; -----------------------------------------------------------------------------
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"
!include "WinVer.nsh"
!include "x64.nsh"

; -----------------------------------------------------------------------------
; Shared Metadata
; -----------------------------------------------------------------------------
!define PRODUCT_PUBLISHER "CasareRPA Team"
!define PRODUCT_WEB_SITE "https://github.com/omerlefaruk/CasareRPA"

; Version can be overridden via command line: /DPRODUCT_VERSION=x.x.x
!ifndef PRODUCT_VERSION
  !define PRODUCT_VERSION "3.0.0"
!endif

; -----------------------------------------------------------------------------
; Compression Settings
; -----------------------------------------------------------------------------
!macro CASARE_COMPRESSION
  SetCompressor /SOLID lzma
  SetCompressorDictSize 64
!macroend

; -----------------------------------------------------------------------------
; Windows Version Check Macro
; -----------------------------------------------------------------------------
; Usage: !insertmacro CASARE_CHECK_WINDOWS
!macro CASARE_CHECK_WINDOWS
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_OK|MB_ICONSTOP "CasareRPA requires Windows 10 or later."
    Abort
  ${EndIf}

  ${IfNot} ${RunningX64}
    MessageBox MB_OK|MB_ICONSTOP "CasareRPA requires 64-bit Windows."
    Abort
  ${EndIf}
!macroend

; -----------------------------------------------------------------------------
; Registry Macros
; -----------------------------------------------------------------------------
; Write uninstall registry entries
; Usage: !insertmacro CASARE_WRITE_UNINSTALL_REG "ProductName" "$INSTDIR\exe.exe"
!macro CASARE_WRITE_UNINSTALL_REG ProductName ExePath
  !define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ProductName}"
  !define APP_PATH_KEY "Software\Microsoft\Windows\CurrentVersion\App Paths\${ProductName}.exe"

  WriteRegStr HKLM "${APP_PATH_KEY}" "" "${ExePath}"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayName" "${ProductName}"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayIcon" "${ExePath}"
  WriteRegStr HKLM "${UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "${UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr HKLM "${UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair" 1

  ; Calculate installed size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "${UNINST_KEY}" "EstimatedSize" "$0"

  !undef UNINST_KEY
  !undef APP_PATH_KEY
!macroend

; Remove uninstall registry entries
; Usage: !insertmacro CASARE_REMOVE_UNINSTALL_REG "ProductName"
!macro CASARE_REMOVE_UNINSTALL_REG ProductName
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${ProductName}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\${ProductName}.exe"
!macroend

; -----------------------------------------------------------------------------
; Config Directory Macro
; -----------------------------------------------------------------------------
; Create CasareRPA config directories
; Usage: !insertmacro CASARE_CREATE_CONFIG_DIRS
!macro CASARE_CREATE_CONFIG_DIRS
  CreateDirectory "$APPDATA\CasareRPA"
  CreateDirectory "$APPDATA\CasareRPA\logs"
  CreateDirectory "$APPDATA\CasareRPA\workflows"
!macroend

; -----------------------------------------------------------------------------
; Shortcut Macros
; -----------------------------------------------------------------------------
; Create Start Menu folder and shortcuts
; Usage: !insertmacro CASARE_CREATE_START_MENU "CasareRPA" links...
!macro CASARE_START_MENU_BEGIN FolderName
  CreateDirectory "$SMPROGRAMS\${FolderName}"
!macroend

; Remove Start Menu folder
; Usage: !insertmacro CASARE_REMOVE_START_MENU "CasareRPA"
!macro CASARE_REMOVE_START_MENU FolderName
  RMDir /r "$SMPROGRAMS\${FolderName}"
!macroend

; -----------------------------------------------------------------------------
; Version Info Macro
; -----------------------------------------------------------------------------
; Add version info to installer
; Usage: !insertmacro CASARE_VERSION_INFO "ProductName" "Description"
!macro CASARE_VERSION_INFO ProductName Description
  VIProductVersion "${PRODUCT_VERSION}.0"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "${ProductName}"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "Comments" "${Description}"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "${PRODUCT_PUBLISHER}"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalCopyright" "MIT License"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "FileDescription" "${ProductName} Installer"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "${PRODUCT_VERSION}"
  VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductVersion" "${PRODUCT_VERSION}"
!macroend

; -----------------------------------------------------------------------------
; Autostart Macro
; -----------------------------------------------------------------------------
; Add to Windows startup
; Usage: !insertmacro CASARE_ADD_AUTOSTART "KeyName" "Command"
!macro CASARE_ADD_AUTOSTART KeyName Command
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${KeyName}" '"${Command}"'
!macroend

; Remove from Windows startup
; Usage: !insertmacro CASARE_REMOVE_AUTOSTART "KeyName"
!macro CASARE_REMOVE_AUTOSTART KeyName
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${KeyName}"
!macroend

; -----------------------------------------------------------------------------
; Config File Write Macro
; -----------------------------------------------------------------------------
; Write YAML config file (call FileOpen first, FileClose after)
; Usage: Push $FileHandle then call
!macro CASARE_WRITE_YAML_HEADER FileHandle
  FileWrite ${FileHandle} "# CasareRPA Configuration$\r$\n"
  FileWrite ${FileHandle} "# Generated by installer$\r$\n"
  FileWrite ${FileHandle} "$\r$\n"
!macroend

; -----------------------------------------------------------------------------
; Uninstall Confirm Macro
; -----------------------------------------------------------------------------
; Show config removal prompt during uninstall
; Usage: !insertmacro CASARE_UNINSTALL_CONFIG_PROMPT
!macro CASARE_UNINSTALL_CONFIG_PROMPT
  MessageBox MB_YESNO|MB_ICONQUESTION "Do you want to remove configuration files and logs?$\n$\n$APPDATA\CasareRPA" IDNO +2
    RMDir /r "$APPDATA\CasareRPA"
!macroend

!endif ; CASARE_COMMON_INCLUDED
