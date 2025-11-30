@echo off
SET PGPASSWORD=postgre
SET PSQL="C:\Program Files\DAZ 3D\PostgreSQL CMS\bin\psql.exe"

echo Creating database...
%PSQL% -U postgres -c "CREATE DATABASE casare_rpa;"

echo Creating user...
%PSQL% -U postgres -c "CREATE USER casare_user WITH PASSWORD 'postgre';"

echo Granting privileges...
%PSQL% -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE casare_rpa TO casare_user;"

echo.
echo PostgreSQL setup complete!
pause
