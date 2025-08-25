Get-Process | Where-Object {
    $_.Modules | Where-Object { $_.FileName -eq "R:\DebugFramework\GNR\752Y31E600117\cr03tppv0162en\20250819\20250819_165019_T10_Core179_Loops\Summary_75AA928800215_Core179_34_IDIPAR_PPV_Data.xlsx" }
}