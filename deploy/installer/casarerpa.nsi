; =============================================================================
; CasareRPA Windows Installer (Canvas + Robot)
; NSIS Script with Modern UI 2
; =============================================================================
; Uses shared macros from nsis/common.nsh
; Build with: makensis /DDIST_DIR=..\..\dist\CasareRPA casarerpa.nsi
; =============================================================================

; Include common definitions and macros
!include "nsis\common.nsh"

; -----------------------------------------------------------------------------
; Application Metadata
; -----------------------------------------------------------------------------
!define PRODUCT_NAME "CasareRPA"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\CasareRPA.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Build output directory (set by build script)
!ifndef DIST_DIR
  !define DIST_DIR "..\..\dist\CasareRPA"
!endif

; -----------------------------------------------------------------------------
; Installer Configuration
; -----------------------------------------------------------------------------
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\..\dist\CasareRPA-${PRODUCT_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
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
!define MUI_ICON "assets\casarerpa.ico"
!define MUI_UNICON "assets\casarerpa.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "assets\installer-banner.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "assets\installer-banner.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "assets\installer-header.bmp"
!define MUI_HEADERIMAGE_RIGHT

; Custom branding text
!define MUI_COMPONENTSPAGE_SMALLDESC
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_UNFINISHPAGE_NOAUTOCLOSE

; -----------------------------------------------------------------------------
; Variables
; -----------------------------------------------------------------------------
Var ORCHESTRATOR_URL
Var API_KEY
Var ROBOT_NAME
Var INSTALL_SERVICE
Var START_WITH_WINDOWS

; Custom page handles
Var Dialog
Var UrlLabel
Var UrlText
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
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY

; Custom Orchestrator Setup Page
Page custom OrchestratorSetupPage OrchestratorSetupPageLeave

!insertmacro MUI_PAGE_INSTFILES

; Finish page with launch option
!define MUI_FINISHPAGE_RUN "$INSTDIR\CasareRPA.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${PRODUCT_NAME}"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "View README"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; -----------------------------------------------------------------------------
; Languages
; -----------------------------------------------------------------------------
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "German"
!insertmacro MUI_LANGUAGE "French"

; -----------------------------------------------------------------------------
; Version Information (from common.nsh)
; -----------------------------------------------------------------------------
!insertmacro CASARE_VERSION_INFO "${PRODUCT_NAME}" "Windows Desktop RPA Platform"

; -----------------------------------------------------------------------------
; Orchestrator Setup Page (Custom)
; -----------------------------------------------------------------------------
Function OrchestratorSetupPage
  !insertmacro MUI_HEADER_TEXT "Orchestrator Connection" "Configure connection to CasareRPA Cloud Orchestrator"

  nsDialogs::Create 1018
  Pop $Dialog

  ${If} $Dialog == error
    Abort
  ${EndIf}

  ; Description text
  ${NSD_CreateLabel} 0 0 100% 24u "Enter the orchestrator URL and API key provided by your administrator.$\n(Leave blank to configure later in Settings)"
  Pop $0

  ; Orchestrator URL
  ${NSD_CreateLabel} 0 35u 80u 12u "Orchestrator URL:"
  Pop $UrlLabel

  ${NSD_CreateText} 85u 33u 215u 14u "wss://orchestrator.example.com/ws/robot"
  Pop $UrlText

  ; API Key
  ${NSD_CreateLabel} 0 55u 80u 12u "API Key:"
  Pop $ApiKeyLabel

  ${NSD_CreatePassword} 85u 53u 215u 14u ""
  Pop $ApiKeyText

  ; Robot Name
  ${NSD_CreateLabel} 0 75u 80u 12u "Robot Name:"
  Pop $RobotNameLabel

  ; Get computer name as default
  ReadEnvStr $0 COMPUTERNAME
  ${NSD_CreateText} 85u 73u 215u 14u "$0-Robot"
  Pop $RobotNameText

  ; Test Connection button
  ${NSD_CreateButton} 85u 95u 80u 18u "Test Connection"
  Pop $TestButton
  ${NSD_OnClick} $TestButton TestConnection

  ; Test result label
  ${NSD_CreateLabel} 170u 97u 130u 12u ""
  Pop $TestResult

  ; Service options section
  ${NSD_CreateGroupBox} 0 120u 100% 50u "Service Options"
  Pop $0

  ${NSD_CreateCheckBox} 10u 135u 280u 12u "Install as Windows Service (runs in background)"
  Pop $INSTALL_SERVICE
  ${NSD_SetState} $INSTALL_SERVICE ${BST_UNCHECKED}

  ${NSD_CreateCheckBox} 10u 150u 280u 12u "Start Robot when Windows starts"
  Pop $START_WITH_WINDOWS
  ${NSD_SetState} $START_WITH_WINDOWS ${BST_CHECKED}

  nsDialogs::Show
FunctionEnd

Function TestConnection
  ${NSD_GetText} $UrlText $ORCHESTRATOR_URL
  ${NSD_GetText} $ApiKeyText $API_KEY

  ${If} $ORCHESTRATOR_URL == ""
    ${NSD_SetText} $TestResult "Please enter URL"
    Return
  ${EndIf}

  ; Simple URL validation
  StrCpy $0 $ORCHESTRATOR_URL 4
  ${If} $0 != "wss:"
    StrCpy $0 $ORCHESTRATOR_URL 3
    ${If} $0 != "ws:"
      ${NSD_SetText} $TestResult "Invalid URL (use ws:// or wss://)"
      Return
    ${EndIf}
  ${EndIf}

  ; Note: Actual connection test would require external tool
  ; For now, just validate format
  ${NSD_SetText} $TestResult "URL format valid"
FunctionEnd

Function OrchestratorSetupPageLeave
  ${NSD_GetText} $UrlText $ORCHESTRATOR_URL
  ${NSD_GetText} $ApiKeyText $API_KEY
  ${NSD_GetText} $RobotNameText $ROBOT_NAME
FunctionEnd

; -----------------------------------------------------------------------------
; Installer Sections
; -----------------------------------------------------------------------------
Section "!Robot Agent (Required)" SEC_ROBOT
  SectionIn RO  ; Required, cannot be deselected

  SetOutPath "$INSTDIR"

  ; Copy main application files
  File /r "${DIST_DIR}\*.*"

  ; Create config directories (from common.nsh)
  !insertmacro CASARE_CREATE_CONFIG_DIRS

  ; Write config file if orchestrator configured
  ${If} $ORCHESTRATOR_URL != ""
    FileOpen $0 "$APPDATA\CasareRPA\config.yaml" w
    FileWrite $0 "# CasareRPA Client Configuration$\r$\n"
    FileWrite $0 "# Generated by installer on ${__DATE__}$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "orchestrator:$\r$\n"
    FileWrite $0 "  url: $ORCHESTRATOR_URL$\r$\n"
    ${If} $API_KEY != ""
      FileWrite $0 "  api_key: $API_KEY$\r$\n"
    ${EndIf}
    FileWrite $0 "$\r$\n"
    FileWrite $0 "robot:$\r$\n"
    FileWrite $0 "  name: $ROBOT_NAME$\r$\n"
    FileWrite $0 "  capabilities:$\r$\n"
    FileWrite $0 "    - browser$\r$\n"
    FileWrite $0 "    - desktop$\r$\n"
    FileWrite $0 "  max_concurrent_jobs: 2$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "logging:$\r$\n"
    FileWrite $0 "  level: INFO$\r$\n"
    FileWrite $0 "  directory: $APPDATA\\CasareRPA\\logs$\r$\n"
    FileClose $0
  ${EndIf}

  ; Create README
  FileOpen $0 "$INSTDIR\README.txt" w
  FileWrite $0 "CasareRPA ${PRODUCT_VERSION}$\r$\n"
  FileWrite $0 "=========================$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "Windows Desktop RPA Platform$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "Quick Start:$\r$\n"
  FileWrite $0 "1. Launch CasareRPA.exe to open the Designer$\r$\n"
  FileWrite $0 "2. Create workflows using the visual node editor$\r$\n"
  FileWrite $0 "3. Run CasareRPA-Robot.exe to connect to orchestrator$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "Configuration:$\r$\n"
  FileWrite $0 "  Config file: $APPDATA\CasareRPA\config.yaml$\r$\n"
  FileWrite $0 "  Logs: $APPDATA\CasareRPA\logs\$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "Documentation: ${PRODUCT_WEB_SITE}$\r$\n"
  FileClose $0

  ; Register uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Registry entries
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\CasareRPA.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\CasareRPA.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "NoModify" 1
  WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "NoRepair" 1

  ; Calculate installed size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

Section "Designer (Workflow Editor)" SEC_DESIGNER
  ; Designer is included with Robot, just create shortcuts
  SetOutPath "$INSTDIR"

  ; Desktop shortcut for Designer
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\CasareRPA.exe" "" "$INSTDIR\CasareRPA.exe" 0

  ; Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME} Designer.lnk" "$INSTDIR\CasareRPA.exe"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME} Robot.lnk" "$INSTDIR\CasareRPA-Robot.exe"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Install Playwright Browsers" SEC_BROWSERS
  SetOutPath "$INSTDIR"

  ; Run Playwright browser installation
  DetailPrint "Installing Playwright browsers (this may take a few minutes)..."

  nsExec::ExecToLog '"$INSTDIR\python.exe" -m playwright install chromium'
  Pop $0
  ${If} $0 != 0
    DetailPrint "Warning: Playwright browser installation may have failed"
    DetailPrint "You can install browsers manually: playwright install"
  ${Else}
    DetailPrint "Playwright browsers installed successfully"
  ${EndIf}
SectionEnd

Section /o "Install as Windows Service" SEC_SERVICE
  ; Install as Windows Service (optional)
  SetOutPath "$INSTDIR"

  DetailPrint "Installing Windows Service..."

  ; Use nssm or sc to install service
  ; Note: Requires nssm.exe to be included or use native sc.exe
  nsExec::ExecToLog 'sc create CasareRPA-Robot binPath= "$INSTDIR\CasareRPA-Robot.exe --service" start= auto DisplayName= "CasareRPA Robot Agent"'
  Pop $0

  ${If} $0 == 0
    DetailPrint "Windows Service installed successfully"
    ; Set service description
    nsExec::ExecToLog 'sc description CasareRPA-Robot "CasareRPA Robot Agent - Executes automation workflows"'
  ${Else}
    DetailPrint "Warning: Service installation failed (code: $0)"
    DetailPrint "You can install the service manually using the install-service.bat script"
  ${EndIf}
SectionEnd

; -----------------------------------------------------------------------------
; Section Descriptions
; -----------------------------------------------------------------------------
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_ROBOT} "Core Robot Agent for executing automation workflows. Required for all installations."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DESIGNER} "Visual workflow designer for creating and editing automation workflows. Includes shortcuts and file associations."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_BROWSERS} "Download and install Chromium browser for web automation. Required for browser-based workflows. (~200MB)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_SERVICE} "Install Robot Agent as a Windows Service. Allows unattended execution without user login."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; -----------------------------------------------------------------------------
; Uninstaller Section
; -----------------------------------------------------------------------------
Section Uninstall
  ; Stop and remove service if installed
  nsExec::ExecToLog 'sc stop CasareRPA-Robot'
  nsExec::ExecToLog 'sc delete CasareRPA-Robot'

  ; Remove files
  RMDir /r "$INSTDIR"

  ; Remove Start Menu shortcuts
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"

  ; Remove Desktop shortcut
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"

  ; Remove registry keys
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

  ; Ask about removing config files (from common.nsh)
  !insertmacro CASARE_UNINSTALL_CONFIG_PROMPT
SectionEnd

; -----------------------------------------------------------------------------
; Installer Functions
; -----------------------------------------------------------------------------
Function .onInit
  ; Check Windows version (from common.nsh)
  !insertmacro CASARE_CHECK_WINDOWS

  ; Check if already installed
  ReadRegStr $0 HKLM "${PRODUCT_DIR_REGKEY}" ""
  ${If} $0 != ""
    MessageBox MB_YESNO|MB_ICONQUESTION "${PRODUCT_NAME} is already installed. Do you want to reinstall?" IDYES continue
    Abort
    continue:
  ${EndIf}

  ; Initialize variables
  StrCpy $ORCHESTRATOR_URL ""
  StrCpy $API_KEY ""
  StrCpy $ROBOT_NAME ""
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO "Are you sure you want to uninstall ${PRODUCT_NAME}?" IDYES +2
  Abort
FunctionEnd
