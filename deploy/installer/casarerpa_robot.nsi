; =============================================================================
; CasareRPA Robot Agent Installer (Lightweight VM Deployment)
; Pre-configured for Supabase Cloud
; =============================================================================
; Uses shared macros from nsis/common.nsh
; Build with: makensis /DDIST_DIR=..\..\dist\CasareRPA-Robot casarerpa_robot.nsi
; =============================================================================

; Include common definitions and macros
!include "nsis\common.nsh"

; -----------------------------------------------------------------------------
; Application Metadata
; -----------------------------------------------------------------------------
!define PRODUCT_NAME "CasareRPA Robot"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\CasareRPA-Robot.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Pre-configured Supabase settings
!define SUPABASE_PROJECT_REF "znaauaswqmurwfglantv"
!define SUPABASE_URL "https://${SUPABASE_PROJECT_REF}.supabase.co"

; Database password (pre-configured for Supabase)
!define DB_PASSWORD "6729Raumafu."

; Build output directory (set by build script)
!ifndef DIST_DIR
  !define DIST_DIR "..\..\dist\CasareRPA-Robot"
!endif

; -----------------------------------------------------------------------------
; Installer Configuration
; -----------------------------------------------------------------------------
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\..\dist\CasareRPA-Robot-${PRODUCT_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES64\CasareRPA"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
RequestExecutionLevel admin

; Compression (from common.nsh)
!insertmacro CASARE_COMPRESSION

; -----------------------------------------------------------------------------
; Modern UI Configuration
; -----------------------------------------------------------------------------
!define MUI_ABORTWARNING

; -----------------------------------------------------------------------------
; Variables
; -----------------------------------------------------------------------------
Var ROBOT_NAME

; Custom page handles
Var Dialog
Var RobotNameLabel
Var RobotNameText

; -----------------------------------------------------------------------------
; Installer Pages
; -----------------------------------------------------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "assets\LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY

; Custom Configuration Page
Page custom ConfigurationPage ConfigurationPageLeave

!insertmacro MUI_PAGE_INSTFILES

; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\CasareRPA-Robot.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Start ${PRODUCT_NAME}"
!define MUI_FINISHPAGE_RUN_PARAMETERS "start --name $ROBOT_NAME"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; -----------------------------------------------------------------------------
; Languages
; -----------------------------------------------------------------------------
!insertmacro MUI_LANGUAGE "English"

; -----------------------------------------------------------------------------
; Version Information (from common.nsh)
; -----------------------------------------------------------------------------
!insertmacro CASARE_VERSION_INFO "${PRODUCT_NAME}" "CasareRPA Robot Agent for VM Deployment"

; -----------------------------------------------------------------------------
; Configuration Page (Custom) - Only Robot Name needed
; -----------------------------------------------------------------------------
Function ConfigurationPage
  !insertmacro MUI_HEADER_TEXT "Robot Configuration" "Enter your robot name"

  nsDialogs::Create 1018
  Pop $Dialog

  ${If} $Dialog == error
    Abort
  ${EndIf}

  ; Description
  ${NSD_CreateLabel} 0 0 100% 36u "This robot connects to CasareRPA Supabase cloud.$\n$\nProject: ${SUPABASE_PROJECT_REF}$\n$\nDatabase connection is pre-configured."
  Pop $0

  ; Robot Name
  ${NSD_CreateLabel} 0 50u 100u 12u "Robot Name:"
  Pop $RobotNameLabel

  ; Get computer name as default
  ReadEnvStr $0 COMPUTERNAME
  ${NSD_CreateText} 105u 48u 195u 14u "$0-Robot"
  Pop $RobotNameText

  ${NSD_CreateLabel} 0 68u 300u 12u "(This name identifies the robot in the orchestrator)"
  Pop $0

  nsDialogs::Show
FunctionEnd

Function ConfigurationPageLeave
  ${NSD_GetText} $RobotNameText $ROBOT_NAME

  ${If} $ROBOT_NAME == ""
    MessageBox MB_OK|MB_ICONEXCLAMATION "Robot name is required!"
    Abort
  ${EndIf}
FunctionEnd

; -----------------------------------------------------------------------------
; Installer Section
; -----------------------------------------------------------------------------
Section "Robot Agent" SEC_ROBOT
  SectionIn RO

  SetOutPath "$INSTDIR"

  ; Copy application files
  File /r "${DIST_DIR}\*.*"

  ; Install Playwright browsers using bundled playwright command
  DetailPrint "Installing Playwright browser (Chromium)..."
  DetailPrint "This may take a few minutes on first install..."

  ; Use the bundled playwright module to install chromium
  ; The frozen app includes playwright, we just need to install the browser binary
  nsExec::ExecToLog 'cmd /c "cd /d "$INSTDIR" && "$INSTDIR\CasareRPA-Robot.exe" --help >nul 2>&1"'
  Pop $0

  ; Try using system Python's playwright if available (more reliable for browser install)
  nsExec::ExecToLog 'cmd /c "playwright install chromium"'
  Pop $0
  ${If} $0 == 0
    DetailPrint "Playwright Chromium browser installed successfully"
  ${Else}
    ; Fallback: Try with python -m playwright
    nsExec::ExecToLog 'cmd /c "python -m playwright install chromium"'
    Pop $0
    ${If} $0 == 0
      DetailPrint "Playwright Chromium browser installed successfully"
    ${Else}
      DetailPrint ""
      DetailPrint "WARNING: Playwright browser install failed."
      DetailPrint "Browser automation will not work until you run:"
      DetailPrint "  playwright install chromium"
      DetailPrint ""
      MessageBox MB_OK|MB_ICONINFORMATION "Playwright browser installation failed.$\n$\nTo enable browser automation, open a terminal and run:$\n  playwright install chromium"
    ${EndIf}
  ${EndIf}

  ; Create config directories (from common.nsh)
  !insertmacro CASARE_CREATE_CONFIG_DIRS

  ; =========================================================================
  ; Create .env file with database configuration
  ; =========================================================================
  DetailPrint "Writing configuration to .env file..."

  ; Write to AppData location (primary - robot loads from here)
  FileOpen $0 "$APPDATA\CasareRPA\.env" w
  FileWrite $0 "# CasareRPA Robot Configuration$\r$\n"
  FileWrite $0 "# Generated by installer$\r$\n"
  FileWrite $0 "# Supabase Project: ${SUPABASE_PROJECT_REF}$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "# Database Password (pre-configured)$\r$\n"
  FileWrite $0 "DB_PASSWORD=${DB_PASSWORD}$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "# Supabase API (optional)$\r$\n"
  FileWrite $0 "SUPABASE_URL=${SUPABASE_URL}$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "# Robot Configuration$\r$\n"
  FileWrite $0 "ROBOT_NAME=$ROBOT_NAME$\r$\n"
  FileWrite $0 "ROBOT_ENVIRONMENT=production$\r$\n"
  FileWrite $0 "CASARE_ENVIRONMENT=production$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "# Logging$\r$\n"
  FileWrite $0 "LOG_LEVEL=INFO$\r$\n"
  FileClose $0

  ; Also copy to install directory (backup, also loaded by frozen exe)
  CopyFiles "$APPDATA\CasareRPA\.env" "$INSTDIR\.env"

  DetailPrint "Configuration saved to $APPDATA\CasareRPA\.env"

  ; Create shortcuts (run exe directly - it loads .env automatically)
  CreateDirectory "$SMPROGRAMS\CasareRPA"
  CreateShortCut "$SMPROGRAMS\CasareRPA\Start Robot.lnk" "$INSTDIR\CasareRPA-Robot.exe" "start --name $ROBOT_NAME" "$INSTDIR\CasareRPA-Robot.exe"
  CreateShortCut "$SMPROGRAMS\CasareRPA\Uninstall Robot.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\CasareRPA Robot.lnk" "$INSTDIR\CasareRPA-Robot.exe" "start --name $ROBOT_NAME" "$INSTDIR\CasareRPA-Robot.exe"

  ; Register uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Registry entries
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\CasareRPA-Robot.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\CasareRPA-Robot.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"

  ; Calculate installed size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

Section "Start with Windows" SEC_AUTOSTART
  ; Add to startup (run exe directly)
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "CasareRPA-Robot" '"$INSTDIR\CasareRPA-Robot.exe" start --name $ROBOT_NAME'
SectionEnd

; -----------------------------------------------------------------------------
; Uninstaller Section
; -----------------------------------------------------------------------------
Section Uninstall
  ; Remove files
  RMDir /r "$INSTDIR"

  ; Remove Start Menu shortcuts
  RMDir /r "$SMPROGRAMS\CasareRPA"

  ; Remove Desktop shortcut
  Delete "$DESKTOP\CasareRPA Robot.lnk"

  ; Remove startup entry
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "CasareRPA-Robot"

  ; Remove registry keys
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

  ; Ask about config (from common.nsh)
  !insertmacro CASARE_UNINSTALL_CONFIG_PROMPT
SectionEnd

; -----------------------------------------------------------------------------
; Installer Functions
; -----------------------------------------------------------------------------
Function .onInit
  ; Check Windows version (from common.nsh)
  !insertmacro CASARE_CHECK_WINDOWS

  StrCpy $ROBOT_NAME ""
FunctionEnd

Function un.onInit
  MessageBox MB_YESNO "Uninstall ${PRODUCT_NAME}?" IDYES +2
  Abort
FunctionEnd
