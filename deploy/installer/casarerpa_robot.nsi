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

; Pre-configured Supabase settings (baked into installer)
!define SUPABASE_PROJECT_REF "znaauaswqmurwfglantv"
!define SUPABASE_URL "https://${SUPABASE_PROJECT_REF}.supabase.co"
; Using Connection Pooler (IPv4) - aws-1-eu-central-1
!define DATABASE_HOST "aws-1-eu-central-1.pooler.supabase.com"
!define DATABASE_USER "postgres.${SUPABASE_PROJECT_REF}"

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
; Icons disabled - placeholder file. Uncomment when valid .ico is available:
; !define MUI_ICON "assets\casarerpa.ico"
; !define MUI_UNICON "assets\casarerpa.ico"

; -----------------------------------------------------------------------------
; Variables
; -----------------------------------------------------------------------------
Var DB_PASSWORD
Var API_KEY
Var ROBOT_NAME

; Custom page handles
Var Dialog
Var PasswordLabel
Var PasswordText
Var ApiKeyLabel
Var ApiKeyText
Var RobotNameLabel
Var RobotNameText
Var TestButton
Var TestResult

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
; Configuration Page (Custom)
; -----------------------------------------------------------------------------
Function ConfigurationPage
  !insertmacro MUI_HEADER_TEXT "Robot Configuration" "Enter your Supabase credentials and robot settings"

  nsDialogs::Create 1018
  Pop $Dialog

  ${If} $Dialog == error
    Abort
  ${EndIf}

  ; Description
  ${NSD_CreateLabel} 0 0 100% 30u "This robot will connect to the CasareRPA cloud orchestrator.$\nEnter your Supabase database password and robot API key."
  Pop $0

  ; Supabase info (read-only)
  ${NSD_CreateLabel} 0 40u 100% 12u "Supabase Project: ${SUPABASE_PROJECT_REF}"
  Pop $0

  ; Database Password
  ${NSD_CreateLabel} 0 60u 100u 12u "Database Password:"
  Pop $PasswordLabel

  ${NSD_CreatePassword} 105u 58u 195u 14u ""
  Pop $PasswordText

  ; API Key
  ${NSD_CreateLabel} 0 82u 100u 12u "Robot API Key:"
  Pop $ApiKeyLabel

  ${NSD_CreatePassword} 105u 80u 195u 14u ""
  Pop $ApiKeyText

  ${NSD_CreateLabel} 0 96u 300u 12u "(Get API key from: python deploy/auto_setup.py setup)"
  Pop $0

  ; Robot Name
  ${NSD_CreateLabel} 0 116u 100u 12u "Robot Name:"
  Pop $RobotNameLabel

  ; Get computer name as default
  ReadEnvStr $0 COMPUTERNAME
  ${NSD_CreateText} 105u 114u 195u 14u "$0-Robot"
  Pop $RobotNameText

  ; Test button
  ${NSD_CreateButton} 0 140u 100u 20u "Test Connection"
  Pop $TestButton
  ${NSD_OnClick} $TestButton TestDatabaseConnection

  ; Test result
  ${NSD_CreateLabel} 110u 144u 190u 12u ""
  Pop $TestResult

  nsDialogs::Show
FunctionEnd

Function TestDatabaseConnection
  ${NSD_GetText} $PasswordText $DB_PASSWORD

  ${If} $DB_PASSWORD == ""
    ${NSD_SetText} $TestResult "Enter password first"
    Return
  ${EndIf}

  ; Basic validation
  StrLen $0 $DB_PASSWORD
  ${If} $0 < 8
    ${NSD_SetText} $TestResult "Password too short"
    Return
  ${EndIf}

  ${NSD_SetText} $TestResult "Password format OK"
FunctionEnd

Function ConfigurationPageLeave
  ${NSD_GetText} $PasswordText $DB_PASSWORD
  ${NSD_GetText} $ApiKeyText $API_KEY
  ${NSD_GetText} $RobotNameText $ROBOT_NAME

  ${If} $DB_PASSWORD == ""
    MessageBox MB_OK|MB_ICONEXCLAMATION "Database password is required!"
    Abort
  ${EndIf}

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

  ; Check for Python and install Playwright browsers via pip
  DetailPrint "Setting up Playwright browsers..."

  ; Try to find Python in PATH or common locations
  nsExec::ExecToLog 'cmd /c "python --version"'
  Pop $0
  ${If} $0 == 0
    DetailPrint "Python found. Installing Playwright..."
    nsExec::ExecToLog 'cmd /c "pip install playwright && playwright install chromium"'
    Pop $0
    ${If} $0 == 0
      DetailPrint "Playwright browsers installed successfully"
    ${Else}
      DetailPrint "Warning: Playwright install failed. You may need to run manually:"
      DetailPrint "  pip install playwright && playwright install chromium"
    ${EndIf}
  ${Else}
    DetailPrint "Python not found. Browser automation will require manual setup."
    DetailPrint "After installing Python, run: pip install playwright && playwright install chromium"
  ${EndIf}

  ; Create config directories (from common.nsh)
  !insertmacro CASARE_CREATE_CONFIG_DIRS

  ; Write .env file with configuration
  FileOpen $0 "$APPDATA\CasareRPA\.env" w
  FileWrite $0 "# CasareRPA Robot Configuration$\r$\n"
  FileWrite $0 "# Generated by installer$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "# Supabase PostgreSQL$\r$\n"
  FileWrite $0 "DATABASE_URL=postgresql://${DATABASE_USER}:$DB_PASSWORD@${DATABASE_HOST}:5432/postgres$\r$\n"
  FileWrite $0 "POSTGRES_URL=postgresql://${DATABASE_USER}:$DB_PASSWORD@${DATABASE_HOST}:5432/postgres$\r$\n"
  FileWrite $0 "PGQUEUER_DB_URL=postgresql://${DATABASE_USER}:$DB_PASSWORD@${DATABASE_HOST}:5432/postgres$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "# Supabase$\r$\n"
  FileWrite $0 "SUPABASE_URL=${SUPABASE_URL}$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "# Robot$\r$\n"
  FileWrite $0 "ROBOT_NAME=$ROBOT_NAME$\r$\n"
  ${If} $API_KEY != ""
    FileWrite $0 "ROBOT_API_KEY=$API_KEY$\r$\n"
  ${EndIf}
  FileWrite $0 "ROBOT_ENVIRONMENT=production$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "# Logging$\r$\n"
  FileWrite $0 "LOG_LEVEL=INFO$\r$\n"
  FileClose $0

  ; Copy .env to install directory too (backup)
  CopyFiles "$APPDATA\CasareRPA\.env" "$INSTDIR\.env"

  ; Create start script
  FileOpen $0 "$INSTDIR\start-robot.bat" w
  FileWrite $0 "@echo off$\r$\n"
  FileWrite $0 "cd /d %~dp0$\r$\n"
  FileWrite $0 "echo Starting CasareRPA Robot: $ROBOT_NAME$\r$\n"
  FileWrite $0 "CasareRPA-Robot.exe start --name $ROBOT_NAME$\r$\n"
  FileWrite $0 "pause$\r$\n"
  FileClose $0

  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\CasareRPA"
  CreateShortCut "$SMPROGRAMS\CasareRPA\Start Robot.lnk" "$INSTDIR\start-robot.bat" "" "$INSTDIR\CasareRPA-Robot.exe"
  CreateShortCut "$SMPROGRAMS\CasareRPA\Uninstall Robot.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\CasareRPA Robot.lnk" "$INSTDIR\start-robot.bat" "" "$INSTDIR\CasareRPA-Robot.exe"

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
  ; Add to startup
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "CasareRPA-Robot" '"$INSTDIR\start-robot.bat"'
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

  StrCpy $DB_PASSWORD ""
  StrCpy $API_KEY ""
  StrCpy $ROBOT_NAME ""
FunctionEnd

Function un.onInit
  MessageBox MB_YESNO "Uninstall ${PRODUCT_NAME}?" IDYES +2
  Abort
FunctionEnd
