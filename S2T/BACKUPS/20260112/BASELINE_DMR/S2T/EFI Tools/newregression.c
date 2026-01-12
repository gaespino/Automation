#include <Uefi.h>
#include <Library/UefiLib.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Library/UefiRuntimeServicesTableLib.h>
#include <Library/MemoryAllocationLib.h>
#include <Library/BaseMemoryLib.h>
#include <Library/PrintLib.h>
#include <Library/ShellLib.h>
#include <Library/FileHandleLib.h>
#include <Protocol/Shell.h>
#include <Protocol/ShellParameters.h>

#define MAX_VAR_SIZE 256
#define MAX_PATH_SIZE 512
#define MAX_COMMAND_SIZE 1024

typedef struct {
    CHAR16 *Name;
    CHAR16 *DefaultValue;
    CHAR16 *CurrentValue;
} CONFIG_VAR;

// Global configuration variables
CONFIG_VAR gConfigVars[] = {
    {L"MERLIN_DRIVE", L"fs0:", NULL},
    {L"MERLIN_DIR", L"fs0:\\", NULL},
    {L"MERLIN", L"MerlinX.efi", NULL},
    {L"MERLIN_EXTRA", L"", NULL},
    {L"DRG_POST_EXE_CMD", L"echo", NULL},
    {L"DRG_RESUME_REGRESSION", L"0", NULL},
    {L"DRG_STOP_ON_FAIL", L"0", NULL},
    {L"DRG_RESET_ON_FAIL", L"0", NULL},
    {L"DRG_START_FRESH", L"0", NULL},
    {L"DRG_CURRENT_SEED", L"NONE", NULL},
    {L"VVAR2", L"0x1000000", NULL},
    {L"VVAR3", L"0x800000", NULL},
    {L"VVAR_EXTRA", L"", NULL},
    {L"DRG_LOOP_FOREVER", L"0", NULL},
    {NULL, NULL, NULL}
};

CHAR16 *gObjDir = NULL;
CHAR16 *gOriginalCwd = NULL;

/**
 * Print help information
 */
VOID
PrintHelp (
    VOID
    )
{
    Print(L"run this script from the directory that contains the seeds.\n");
    Print(L"Usage:\n");
    Print(L"    runregression.efi <OBJ DIR> : runs all OBJs in the directory\n");
    Print(L"    runregression.efi <OBJ DIR> <match string_1> <match string_n>: Runs all OBJS that contain the <string>\n");
    Print(L"Overrides are done via EFI VARIABLES: (you will likely need to set up MERLIN VARIABLES!!!!)\n");
    Print(L"setup variables via \"set <sname> <value>\"\n");
    Print(L"DRG_RESUME_REGRESSION: if set == 1, resume regression starting with seed after %%CURRENT_SEED%%\n");
    Print(L"MERLIN_DIR: Directory where MerlinX exists  (default = fs0:\\)\n");
    Print(L"MERLIN_DRIVE: Drive where MERLIN_DIR exists (default = fs0:)\n");
    Print(L"MERLIN: Name of MerlinX : (default = merlinx)\n");
    Print(L"DRG_START_FRESH : If set, delete log files and var files.\n");
    Print(L"DRG_CLEAN_ALL : If set, resets all variables\n");
    Print(L"DRG_CURRENT_SEED: Current seed being run. Used for resuming regression\n");
    Print(L"VVAR2 : Dragon VVAR 2 input. 1 value\n");
    Print(L"VVAR3 : Dragon VVAR 3 input. 1 value\n");
    Print(L"VVAR_EXTRA : Additional vvar parameters. Must be <VVAR> <VVAR_VAL>. Use quotes around VVAR VVAR_VAL when setting it\n");
    Print(L"MERLIN_EXTRA : Additional merlin parameters.\n");
    Print(L"DRG_LOOP_FOREVER: if set==1, keep running forever\n");
    Print(L"DRG_STOP_ON_FAIL--> if set==1, exit on first fail ( when <obj>.var is present)\n");
    Print(L"DRG_RESET_ON_FAIL--> if set==1, resets system on first fail ( when <obj>.var is present)\n");
    Print(L"DRG_POST_EXE_CMD --> will execute this command on every loop\n");
}

/**
 * Get EFI variable value
 */
EFI_STATUS
GetEfiVariable (
    IN  CHAR16    *VariableName,
    OUT CHAR16    **Value
    )
{
    EFI_STATUS Status;
    UINTN      DataSize = 0;
    CHAR16     *Data = NULL;

    // Get variable size
    Status = gRT->GetVariable(
        VariableName,
        &gEfiGlobalVariableGuid,
        NULL,
        &DataSize,
        NULL
    );

    if (Status == EFI_BUFFER_TOO_SMALL) {
        Data = AllocatePool(DataSize);
        if (Data == NULL) {
            return EFI_OUT_OF_RESOURCES;
        }

        Status = gRT->GetVariable(
            VariableName,
            &gEfiGlobalVariableGuid,
            NULL,
            &DataSize,
            Data
        );

        if (EFI_ERROR(Status)) {
            FreePool(Data);
            return Status;
        }

        *Value = Data;
        return EFI_SUCCESS;
    }

    return Status;
}

/**
 * Set EFI variable value
 */
EFI_STATUS
SetEfiVariable (
    IN CHAR16 *VariableName,
    IN CHAR16 *Value
    )
{
    return gRT->SetVariable(
        VariableName,
        &gEfiGlobalVariableGuid,
        EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS | EFI_VARIABLE_RUNTIME_ACCESS,
        StrSize(Value),
        Value
    );
}

/**
 * Initialize configuration variables
 */
EFI_STATUS
InitializeConfigVars (
    VOID
    )
{
    UINTN Index;
    CHAR16 *VarValue;
    EFI_STATUS Status;

    for (Index = 0; gConfigVars[Index].Name != NULL; Index++) {
        Status = GetEfiVariable(gConfigVars[Index].Name, &VarValue);
        
        if (EFI_ERROR(Status)) {
            // Variable doesn't exist, use default
            gConfigVars[Index].CurrentValue = AllocateCopyPool(
                StrSize(gConfigVars[Index].DefaultValue),
                gConfigVars[Index].DefaultValue
            );
        } else {
            // Variable exists, use its value
            gConfigVars[Index].CurrentValue = VarValue;
        }

        if (gConfigVars[Index].CurrentValue == NULL) {
            return EFI_OUT_OF_RESOURCES;
        }
    }

    return EFI_SUCCESS;
}

/**
 * Get configuration variable value
 */
CHAR16 *
GetConfigVar (
    IN CHAR16 *VarName
    )
{
    UINTN Index;

    for (Index = 0; gConfigVars[Index].Name != NULL; Index++) {
        if (StrCmp(gConfigVars[Index].Name, VarName) == 0) {
            return gConfigVars[Index].CurrentValue;
        }
    }

    return NULL;
}

/**
 * Set configuration variable value
 */
EFI_STATUS
SetConfigVar (
    IN CHAR16 *VarName,
    IN CHAR16 *Value
    )
{
    UINTN Index;

    for (Index = 0; gConfigVars[Index].Name != NULL; Index++) {
        if (StrCmp(gConfigVars[Index].Name, VarName) == 0) {
            if (gConfigVars[Index].CurrentValue != NULL) {
                FreePool(gConfigVars[Index].CurrentValue);
            }
            gConfigVars[Index].CurrentValue = AllocateCopyPool(StrSize(Value), Value);
            return SetEfiVariable(VarName, Value);
        }
    }

    return EFI_NOT_FOUND;
}

/**
 * Execute shell command
 */
EFI_STATUS
ExecuteCommand (
    IN CHAR16 *Command
    )
{
    EFI_STATUS Status;
    EFI_SHELL_PROTOCOL *Shell;

    Status = gBS->LocateProtocol(&gEfiShellProtocolGuid, NULL, (VOID**)&Shell);
    if (EFI_ERROR(Status)) {
        return Status;
    }

    Print(L"Executing: %s\n", Command);
    return Shell->Execute(NULL, Command, NULL, NULL);
}

/**
 * Check if file exists
 */
BOOLEAN
FileExists (
    IN CHAR16 *FilePath
    )
{
    EFI_STATUS Status;
    SHELL_FILE_HANDLE FileHandle;

    Status = ShellOpenFileByName(FilePath, &FileHandle, EFI_FILE_MODE_READ, 0);
    if (!EFI_ERROR(Status)) {
        ShellCloseFile(&FileHandle);
        return TRUE;
    }

    return FALSE;
}

/**
 * Delete file
 */
EFI_STATUS
DeleteFile (
    IN CHAR16 *FilePath
    )
{
    EFI_STATUS Status;
    SHELL_FILE_HANDLE FileHandle;

    Status = ShellOpenFileByName(FilePath, &FileHandle, EFI_FILE_MODE_READ | EFI_FILE_MODE_WRITE, 0);
    if (!EFI_ERROR(Status)) {
        Status = ShellDeleteFile(&FileHandle);
    }

    return Status;
}

/**
 * Clean up files for fresh start
 */
EFI_STATUS
CleanupFiles (
    VOID
    )
{
    CHAR16 FilePath[MAX_PATH_SIZE];

    Print(L"DRG_START_FRESH is set.\n");
    Print(L"  removing *.var, *.run *.hng fail.txt log.txt\n");

    // Delete various file types
    UnicodeSPrint(FilePath, sizeof(FilePath), L"%s\\*.var", gObjDir);
    ShellDeleteFileByName(FilePath);

    UnicodeSPrint(FilePath, sizeof(FilePath), L"%s\\*.run", gObjDir);
    ShellDeleteFileByName(FilePath);

    UnicodeSPrint(FilePath, sizeof(FilePath), L"%s\\*.hng", gObjDir);
    ShellDeleteFileByName(FilePath);

    UnicodeSPrint(FilePath, sizeof(FilePath), L"%s\\fail.txt", gObjDir);
    DeleteFile(FilePath);

    UnicodeSPrint(FilePath, sizeof(FilePath), L"%s\\log.txt", gObjDir);
    DeleteFile(FilePath);

    SetConfigVar(L"DRG_START_FRESH", L"0");

    return EFI_SUCCESS;
}

/**
 * Process a single seed file
 */
EFI_STATUS
ProcessSeed (
    IN CHAR16 *SeedFile
    )
{
    EFI_STATUS Status;
    CHAR16 Command[MAX_COMMAND_SIZE];
    CHAR16 LogEntry[MAX_COMMAND_SIZE];
    CHAR16 VarFile[MAX_PATH_SIZE];
    CHAR16 HngFile[MAX_PATH_SIZE];
    CHAR16 SkpFile[MAX_PATH_SIZE];
    CHAR16 FailFile[MAX_PATH_SIZE];
    CHAR16 LogFile[MAX_PATH_SIZE];
    CHAR16 *MerlinCmd, *Vvar2, *Vvar3, *VvarExtra, *MerlinExtra;

    // Check if seed should be skipped
    UnicodeSPrint(SkpFile, sizeof(SkpFile), L"%s.skp", SeedFile);
    if (FileExists(SkpFile)) {
        return EFI_SUCCESS; // Skip this seed
    }

    // Check if seed file exists
    if (!FileExists(SeedFile)) {
        Print(L"%s not found!!!\n", SeedFile);
        return EFI_NOT_FOUND;
    }

    // Set current seed
    SetConfigVar(L"DRG_CURRENT_SEED", SeedFile);

    // Build VVAR string
    Vvar2 = GetConfigVar(L"VVAR2");
    Vvar3 = GetConfigVar(L"VVAR3");
    VvarExtra = GetConfigVar(L"VVAR_EXTRA");
    MerlinExtra = GetConfigVar(L"MERLIN_EXTRA");

    // Create hang file
    UnicodeSPrint(HngFile, sizeof(HngFile), L"%s.hng", SeedFile);
    UnicodeSPrint(LogEntry, sizeof(LogEntry), L"running %s", SeedFile);
    ShellPrintToFile(HngFile, LogEntry);

    // Build and execute MERLIN command
    UnicodeSPrint(Command, sizeof(Command), 
        L"%s %s -a %s -d 2 %s 3 %s %s",
        GetConfigVar(L"MERLIN"),
        MerlinExtra,
        SeedFile,
        Vvar2,
        Vvar3,
        VvarExtra
    );

    Print(L"running \"%s\"\n", Command);

    // Log the command
    UnicodeSPrint(LogFile, sizeof(LogFile), L"%s\\log.txt", gObjDir);
    UnicodeSPrint(LogEntry, sizeof(LogEntry), L"running \"%s\"\n", Command);
    ShellPrintToFile(LogFile, LogEntry);

    Status = ExecuteCommand(Command);

    // Remove hang file
    DeleteFile(HngFile);

    // Check for failure (.var file)
    UnicodeSPrint(VarFile, sizeof(VarFile), L"%s.var", SeedFile);
    if (FileExists(VarFile)) {
        // Seed failed
        UnicodeSPrint(FailFile, sizeof(FailFile), L"%s\\fail.txt", gObjDir);
        UnicodeSPrint(LogEntry, sizeof(LogEntry), L"!!!!!!!!!!!!!!!!!\n%s FAILED\n", SeedFile);
        ShellPrintToFile(FailFile, LogEntry);

        Print(L"FOUND %s\n", VarFile);
        Print(L"!!! %s FAILED !!!\n", SeedFile);

        if (StrCmp(GetConfigVar(L"DRG_RESET_ON_FAIL"), L"1") == 0) {
            Print(L"!!! DRG_RESET_ON_FAIL is set... RESETTING SYSTEM !!!\n");
            gBS->Stall(3000000); // 3 second delay
            gRT->ResetSystem(EfiResetCold, EFI_SUCCESS, 0, NULL);
        }

        if (StrCmp(GetConfigVar(L"DRG_STOP_ON_FAIL"), L"1") == 0) {
            Print(L"!!! DRG_STOP_ON_FAIL is set. Stopping regression!!!\n");
            return EFI_ABORTED;
        }
    } else {
        // Seed passed
        UnicodeSPrint(LogEntry, sizeof(LogEntry), L"%s PASSED\n", SeedFile);
        ShellPrintToFile(LogFile, LogEntry);
    }

    // Execute post command
    ExecuteCommand(GetConfigVar(L"DRG_POST_EXE_CMD"));

    return EFI_SUCCESS;
}

/**
 * Run regression on matching files
 */
EFI_STATUS
RunRegression (
    IN CHAR16 *Pattern
    )
{
    EFI_STATUS Status;
    EFI_SHELL_FILE_INFO *FileList = NULL;
    EFI_SHELL_FILE_INFO *Node;
    CHAR16 SearchPattern[MAX_PATH_SIZE];
    CHAR16 FailFile[MAX_PATH_SIZE];

    Print(L"Starting regression\n");

    // Initialize fail.txt
    UnicodeSPrint(FailFile, sizeof(FailFile), L"%s\\fail.txt", gObjDir);
    ShellPrintToFile(FailFile, L"**************\n");

    // Build search pattern
    if (Pattern != NULL) {
        UnicodeSPrint(SearchPattern, sizeof(SearchPattern), L"%s\\*%s*.obj", gObjDir, Pattern);
    } else {
        UnicodeSPrint(SearchPattern, sizeof(SearchPattern), L"%s\\*.obj", gObjDir);
    }

    do {
        // Get file list
        Status = ShellOpenFileMetaArg(SearchPattern, EFI_FILE_MODE_READ, &FileList);
        if (EFI_ERROR(Status)) {
            Print(L"No files found matching pattern: %s\n", SearchPattern);
            break;
        }

        // Process each file
        for (Node = (EFI_SHELL_FILE_INFO *)GetFirstNode(&FileList->Link);
             !IsNull(&FileList->Link, &Node->Link);
             Node = (EFI_SHELL_FILE_INFO *)GetNextNode(&FileList->Link, &Node->Link)) {

            if (Node->Info->Attribute & EFI_FILE_DIRECTORY) {
                continue; // Skip directories
            }

            Status = ProcessSeed(Node->FullName);
            if (Status == EFI_ABORTED) {
                // Stop on fail was triggered
                break;
            }
        }

        // Clean up file list
        if (FileList != NULL) {
            ShellCloseFileMetaArg(&FileList);
        }

    } while (StrCmp(GetConfigVar(L"DRG_LOOP_FOREVER"), L"1") == 0);

    return Status;
}

/**
 * Main entry point
 */
EFI_STATUS
EFIAPI
UefiMain (
    IN EFI_HANDLE        ImageHandle,
    IN EFI_SYSTEM_TABLE  *SystemTable
    )
{
    EFI_STATUS Status;
    EFI_SHELL_PARAMETERS_PROTOCOL *ShellParameters;
    UINTN Argc;
    CHAR16 **Argv;
    UINTN ArgIndex;
    CHAR16 MerlinPath[MAX_PATH_SIZE];

    Print(L"**************************************\n");
    Print(L"***** runregression version 1.13 *****\n");
    Print(L"***** contact: Brent Calhoon     *****\n");
    Print(L"**************************************\n");

    // Get command line parameters
    Status = gBS->HandleProtocol(
        ImageHandle,
        &gEfiShellParametersProtocolGuid,
        (VOID**)&ShellParameters
    );

    if (EFI_ERROR(Status)) {
        Print(L"Failed to get shell parameters\n");
        return Status;
    }

    Argc = ShellParameters->Argc;
    Argv = ShellParameters->Argv;

    // Check for help
    if (Argc < 2 || StrCmp(Argv[1], L"help") == 0) {
        PrintHelp();
        return EFI_SUCCESS;
    }

    // Initialize configuration variables
    Status = InitializeConfigVars();
    if (EFI_ERROR(Status)) {
        Print(L"Failed to initialize configuration variables\n");
        return Status;
    }

    // Set OBJ directory
    gObjDir = Argv[1];
    if (!FileExists(gObjDir)) {
        Print(L"!!!!! OBJ_DIR does not exist: %s !!!!\n", gObjDir);
        PrintHelp();
        return EFI_NOT_FOUND;
    }

    Print(L"running seeds in %s\n", gObjDir);

    // Save current directory
    gOriginalCwd = ShellGetCurrentDir(NULL);

    // Switch to MERLIN directory
    Print(L"switching to drive %s\n", GetConfigVar(L"MERLIN_DRIVE"));
    ShellSetCurrentDir(NULL, GetConfigVar(L"MERLIN_DRIVE"));
    
    Print(L"CHANGING TO MERLINX DIR: %s\n", GetConfigVar(L"MERLIN_DIR"));
    ShellSetCurrentDir(NULL, GetConfigVar(L"MERLIN_DIR"));

    // Verify MERLIN exists
    UnicodeSPrint(MerlinPath, sizeof(MerlinPath), L"%s", GetConfigVar(L"MERLIN"));
    if (!FileExists(MerlinPath)) {
        Print(L"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
        Print(L"!!!!! MERLINX is not FOUND          !!!!!\n");
        Print(L"!!!!! MERLINX = %s            !!!!!\n", GetConfigVar(L"MERLIN"));
        Print(L"!!!!! MERLIN_DRIVE = %s !!!!!\n", GetConfigVar(L"MERLIN_DRIVE"));
        Print(L"!!!!! MERLIN_DIR = %s     !!!!!\n", GetConfigVar(L"MERLIN_DIR"));
        Print(L"!!!!!                               !!!!!\n");
        Print(L"!!!!! EXITING......                 !!!!!\n");
        Print(L"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
        goto Done;
    }

    // Handle fresh start
    if (StrCmp(GetConfigVar(L"DRG_START_FRESH"), L"1") == 0) {
        CleanupFiles();
    }

    // Run regression for each pattern
    if (Argc == 2) {
        // No pattern specified, run all
        Status = RunRegression(NULL);
    } else {
        // Run for each specified pattern
        for (ArgIndex = 2; ArgIndex < Argc; ArgIndex++) {
            Status = RunRegression(Argv[ArgIndex]);
            if (Status == EFI_ABORTED) {
                break; // Stop on fail
            }
        }
    }

    if (Status == EFI_ABORTED) {
        Print(L"Test Failed\n");
    } else {
        Print(L"Test Complete\n");
    }

Done:
    Print(L"regression info in %s\\log.txt\n", gObjDir);
    Print(L"fail info in %s\\fail.txt\n", gObjDir);
    
    if (gOriginalCwd != NULL) {
        Print(L"CHANGING BACK TO DIR: %s\n", gOriginalCwd);
        ShellSetCurrentDir(NULL, gOriginalCwd);
    }

    return Status;
}