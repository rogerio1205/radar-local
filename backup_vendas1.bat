@echo off

set DATA=%date:~-4,4%-%date:~3,2%-%date:~0,2%
set DEST=C:\BACKUP_VENDAS1\Vendas1_%DATA%.zip

powershell Compress-Archive -Path "C:\Users\User\Vendas1\*" -DestinationPath "%DEST%" -Force

echo.
echo ================================
echo BACKUP CRIADO COM SUCESSO
echo %DEST%
echo ================================
pause